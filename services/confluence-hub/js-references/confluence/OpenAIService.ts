import OpenAI from 'openai';
import { IConvertedDocument, ConvertedDocument } from '../models/ConvertedDocument';
import { VectorSearchService } from './VectorSearchService';

export interface SearchResult {
  document: IConvertedDocument;
  score: number;
  answer?: string;
}

export class OpenAIService {
  private openai: OpenAI;
  private vectorSearch: VectorSearchService;
  private initialized = false;

  constructor() {
    const apiKey = process.env.ANALYTICS_OPENAI_API_KEY;
    if (!apiKey) {
      throw new Error('ANALYTICS_OPENAI_API_KEY environment variable is not set');
    }

    this.openai = new OpenAI({ apiKey });
    this.vectorSearch = new VectorSearchService();
  }

  async initialize(): Promise<void> {
    if (this.initialized) return;

    await this.vectorSearch.initialize();
    this.initialized = true;
  }

  async generateEmbedding(text: string): Promise<number[]> {
    try {
      // Truncate text if it's too long (max ~8000 tokens, roughly 32000 chars)
      const truncatedText = text.slice(0, 32000);

      const response = await this.openai.embeddings.create({
        model: 'text-embedding-3-small',
        input: truncatedText,
        encoding_format: 'float',
      });

      return response.data[0]?.embedding || [];
    } catch (error) {
      console.error('Error generating embedding:', error);
      throw new Error(`Failed to generate embedding: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  async searchDocuments(query: string, limit: number = 5, minScore: number = 0.15): Promise<SearchResult[]> {
    // Ensure service is initialized
    if (!this.initialized) {
      await this.initialize();
    }

    // Generate embedding for the query
    const queryEmbedding = await this.generateEmbedding(query);

    // Search for similar documents using vector search
    const similarDocs = await this.vectorSearch.searchSimilar(
      queryEmbedding,
      limit * 2, // Get more candidates for better results
      minScore
    );

    if (similarDocs.length === 0) {
      return [];
    }

    // Fetch full documents from MongoDB
    const documentIds = similarDocs.map(d => d.documentId);
    const documents = await ConvertedDocument.find({
      _id: { $in: documentIds },
    }).lean();

    // Map documents with their similarity scores
    const docsWithScores: SearchResult[] = documents.map(doc => {
      const match = similarDocs.find(s => s.documentId === doc._id.toString());
      return {
        document: doc,
        score: match?.score || 0,
      };
    });

    // Sort by score and limit to requested number
    const topDocs = docsWithScores.sort((a, b) => b.score - a.score).slice(0, limit);

    // Generate AI answer based on top documents
    if (topDocs.length > 0) {
      try {
        const answer = await this.generateAnswer(
          query,
          topDocs.map(d => d.document)
        );
        // Add answer to the first result
        if (topDocs[0]) {
          topDocs[0].answer = answer;
        }
      } catch (error) {
        console.error('Error generating answer:', error);
        // Continue without answer if generation fails
      }
    }

    return topDocs;
  }

  async generateAnswer(query: string, documents: IConvertedDocument[]): Promise<string> {
    // Prepare context from documents (limit to prevent token overflow)
    const context = documents
      .slice(0, 3) // Use top 3 documents for context
      .map((doc, i) => {
        const contentPreview = doc.content.slice(0, 2000);
        return `Document ${i + 1}: "${doc.title}"
Source: ${doc.metadata.spaceKey}
Content:
${contentPreview}${doc.content.length > 2000 ? '...' : ''}`;
      })
      .join('\n\n---\n\n');

    try {
      const response = await this.openai.chat.completions.create({
        model: 'gpt-4o',
        messages: [
          {
            role: 'system',
            content: `You are a helpful assistant that answers questions based on the provided Confluence documentation.
Always cite which document(s) you are referencing by mentioning the document title.
If the answer cannot be found in the provided documents, say so clearly.
Keep your answers concise and relevant to the question.`,
          },
          {
            role: 'user',
            content: `Based on the following Confluence documents, please answer this question: ${query}

Context from relevant documents:
${context}`,
          },
        ],
        temperature: 0.3,
        max_tokens: 1000,
      });

      return response.choices[0]?.message?.content || 'Unable to generate answer';
    } catch (error) {
      console.error('Error calling OpenAI chat completion:', error);
      throw new Error(`Failed to generate answer: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  async processDocumentEmbedding(documentId: string): Promise<void> {
    try {
      const doc = await ConvertedDocument.findById(documentId);
      if (!doc) {
        throw new Error(`Document not found: ${documentId}`);
      }

      // Generate embedding for title + content
      const textToEmbed = `${doc.title}\n\n${doc.content}`;
      const embedding = await this.generateEmbedding(textToEmbed);

      // Update document with embedding
      doc.embedding = embedding;
      doc.embeddingVersion = 'text-embedding-3-small-v1';
      doc.embeddingGeneratedAt = new Date();
      await doc.save();

      // Update vector search cache if initialized
      if (this.initialized) {
        await this.vectorSearch.updateVector(documentId, embedding, doc.title, doc.confluencePageId);
      }

      console.log(`Generated embedding for document: ${doc.title}`);
    } catch (error) {
      console.error(`Error processing embedding for document ${documentId}:`, error);
      throw error;
    }
  }

  async processAllDocuments(batchSize: number = 5): Promise<void> {
    try {
      // Find documents without embeddings
      const documents = await ConvertedDocument.find({
        $or: [{ embedding: { $exists: false } }, { embedding: { $size: 0 } }],
      }).select('_id title');

      console.log(`Found ${documents.length} documents without embeddings`);

      // Process in batches to avoid rate limits
      for (let i = 0; i < documents.length; i += batchSize) {
        const batch = documents.slice(i, i + batchSize);

        await Promise.all(batch.map(doc => this.processDocumentEmbedding((doc._id as any).toString())));

        console.log(`Processed ${Math.min(i + batchSize, documents.length)}/${documents.length} documents`);

        // Add delay to respect rate limits (3000 RPM for embeddings)
        if (i + batchSize < documents.length) {
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
      }

      // Reinitialize vector search to load all new embeddings
      if (this.initialized) {
        await this.vectorSearch.initialize();
      }

      console.log('Completed processing all documents');
    } catch (error) {
      console.error('Error processing documents:', error);
      throw error;
    }
  }
}

export default OpenAIService;

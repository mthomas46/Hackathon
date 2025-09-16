import { ConvertedDocument } from '../models/ConvertedDocument';

export interface DocumentVector {
  documentId: string;
  embedding: number[];
  title: string;
  confluencePageId: string;
}

export interface SearchMatch {
  documentId: string;
  score: number;
  title: string;
}

export class VectorSearchService {
  private vectorCache: Map<string, DocumentVector> = new Map();
  private initialized = false;

  async initialize(): Promise<void> {
    console.log('Initializing vector search service...');

    try {
      // Clear existing cache
      this.vectorCache.clear();

      // Load all documents with embeddings
      const documents = await ConvertedDocument.find(
        {
          embedding: { $exists: true, $ne: [] },
        },
        {
          _id: 1,
          embedding: 1,
          title: 1,
          confluencePageId: 1,
        }
      ).lean();

      // Populate cache
      for (const doc of documents) {
        if (doc.embedding && doc.embedding.length === 1536) {
          this.vectorCache.set(doc._id.toString(), {
            documentId: doc._id.toString(),
            embedding: doc.embedding,
            title: doc.title,
            confluencePageId: doc.confluencePageId,
          });
        }
      }

      this.initialized = true;
      console.log(`Vector search initialized with ${this.vectorCache.size} document embeddings`);
    } catch (error) {
      console.error('Error initializing vector search:', error);
      throw new Error(`Failed to initialize vector search: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  private cosineSimilarity(a: number[], b: number[]): number {
    if (a.length !== b.length) {
      throw new Error('Vectors must have the same length');
    }

    let dotProduct = 0;
    let normA = 0;
    let normB = 0;

    for (let i = 0; i < a.length; i++) {
      dotProduct += (a[i] || 0) * (b[i] || 0);
      normA += (a[i] || 0) * (a[i] || 0);
      normB += (b[i] || 0) * (b[i] || 0);
    }

    const denominator = Math.sqrt(normA) * Math.sqrt(normB);

    // Avoid division by zero
    if (denominator === 0) {
      return 0;
    }

    return dotProduct / denominator;
  }

  async searchSimilar(queryEmbedding: number[], limit: number = 5, minScore: number = 0.15): Promise<SearchMatch[]> {
    // Ensure service is initialized
    if (!this.initialized) {
      await this.initialize();
    }

    if (queryEmbedding.length !== 1536) {
      throw new Error('Query embedding must have exactly 1536 dimensions');
    }

    const results: SearchMatch[] = [];

    // Calculate similarity for all cached documents
    for (const [docId, docVector] of this.vectorCache) {
      try {
        const score = this.cosineSimilarity(queryEmbedding, docVector.embedding);

        if (score >= minScore) {
          results.push({
            documentId: docId,
            score: score,
            title: docVector.title,
          });
        }
      } catch (error) {
        console.error(`Error calculating similarity for document ${docId}:`, error);
        // Continue with other documents
      }
    }

    // Sort by score in descending order and limit results
    return results.sort((a, b) => b.score - a.score).slice(0, limit);
  }

  async updateVector(documentId: string, embedding: number[], title: string, confluencePageId: string): Promise<void> {
    if (embedding.length !== 1536) {
      throw new Error('Embedding must have exactly 1536 dimensions');
    }

    this.vectorCache.set(documentId, {
      documentId,
      embedding,
      title,
      confluencePageId,
    });

    console.log(`Updated vector cache for document: ${title}`);
  }

  removeVector(documentId: string): void {
    if (this.vectorCache.delete(documentId)) {
      console.log(`Removed vector for document: ${documentId}`);
    }
  }

  getCacheSize(): number {
    return this.vectorCache.size;
  }

  isInitialized(): boolean {
    return this.initialized;
  }

  getMemoryUsage(): string {
    // Estimate memory usage (each embedding is ~6KB)
    const estimatedBytes = this.vectorCache.size * 1536 * 4; // 4 bytes per float
    const estimatedMB = (estimatedBytes / (1024 * 1024)).toFixed(2);
    return `${estimatedMB} MB`;
  }

  async refresh(): Promise<void> {
    console.log('Refreshing vector cache...');
    this.initialized = false;
    await this.initialize();
  }
}

export default VectorSearchService;

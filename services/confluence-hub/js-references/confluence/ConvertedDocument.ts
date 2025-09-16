import mongoose, { Schema, Document } from 'mongoose';

export interface IConvertedDocument extends Document {
  sessionId: string;
  confluencePageId: string;
  title: string;
  content: string;
  embedding?: number[];
  embeddingVersion?: string;
  embeddingGeneratedAt?: Date;
  metadata: {
    originalUrl: string;
    spaceKey: string;
    parentPageId?: string;
    lastModified: Date;
    author: string;
    version: number;
  };
  filePath: string;
  createdAt: Date;
  updatedAt: Date;
}

const convertedDocumentSchema = new Schema<IConvertedDocument>(
  {
    sessionId: {
      type: String,
      required: true,
    },
    confluencePageId: {
      type: String,
      required: true,
    },
    title: {
      type: String,
      required: true,
    },
    content: {
      type: String,
      required: true,
    },
    metadata: {
      originalUrl: {
        type: String,
        required: true,
      },
      spaceKey: {
        type: String,
        required: true,
      },
      parentPageId: {
        type: String,
      },
      lastModified: {
        type: Date,
        required: true,
      },
      author: {
        type: String,
        required: true,
      },
      version: {
        type: Number,
        required: true,
        min: 1,
      },
    },
    filePath: {
      type: String,
      required: true,
    },
    embedding: {
      type: [Number],
      required: false,
      index: false,
      validate: {
        validator: function (v: number[]) {
          // Allow undefined, null, or arrays with exactly 1536 elements
          // Also allow empty arrays for backward compatibility
          return v === undefined || v === null || (Array.isArray(v) && (v.length === 0 || v.length === 1536));
        },
        message: 'Embedding must have exactly 1536 dimensions or be empty',
      },
    },
    embeddingVersion: {
      type: String,
      default: 'text-embedding-3-small-v1',
    },
    embeddingGeneratedAt: {
      type: Date,
    },
  },
  {
    timestamps: true,
    collection: 'converted_documents',
  }
);

// Indexes for performance
convertedDocumentSchema.index({ sessionId: 1 });
convertedDocumentSchema.index({ confluencePageId: 1 }, { unique: true });
convertedDocumentSchema.index({ 'metadata.spaceKey': 1 });
convertedDocumentSchema.index({ title: 'text', content: 'text' });

export const ConvertedDocument = mongoose.model<IConvertedDocument>('ConvertedDocument', convertedDocumentSchema);

// Contains AI-generated edits.

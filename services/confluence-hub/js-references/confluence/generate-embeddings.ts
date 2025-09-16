#!/usr/bin/env tsx

import dotenv from 'dotenv';
import mongoose from 'mongoose';
import { ConvertedDocument } from '../src/models/ConvertedDocument';
import OpenAIService from '../src/services/OpenAIService';
import { config } from '../src/config/app.config';

// Load environment variables
dotenv.config();

async function generateEmbeddings() {
  console.log('=== Starting Embedding Generation Script ===\n');

  try {
    // Connect to MongoDB
    console.log('Connecting to MongoDB...');
    await mongoose.connect(config.mongodb.connectionString);
    console.log('✓ Connected to MongoDB\n');

    // Initialize OpenAI service
    console.log('Initializing OpenAI service...');
    const openAIService = new OpenAIService();
    await openAIService.initialize();
    console.log('✓ OpenAI service initialized\n');

    // Get statistics
    const totalDocuments = await ConvertedDocument.countDocuments();
    const documentsWithEmbeddings = await ConvertedDocument.countDocuments({
      embedding: { $exists: true, $ne: [] },
    });
    const documentsWithoutEmbeddings = await ConvertedDocument.countDocuments({
      $or: [{ embedding: { $exists: false } }, { embedding: { $size: 0 } }],
    });

    console.log('=== Document Statistics ===');
    console.log(`Total documents: ${totalDocuments}`);
    console.log(`Documents with embeddings: ${documentsWithEmbeddings}`);
    console.log(`Documents without embeddings: ${documentsWithoutEmbeddings}\n`);

    if (documentsWithoutEmbeddings === 0) {
      console.log('All documents already have embeddings!');
      await mongoose.disconnect();
      process.exit(0);
    }

    // Ask for confirmation
    const readline = require('readline').createInterface({
      input: process.stdin,
      output: process.stdout,
    });

    const answer = await new Promise<string>(resolve => {
      readline.question(`Generate embeddings for ${documentsWithoutEmbeddings} documents? (yes/no): `, resolve);
    });

    readline.close();

    if (answer.toLowerCase() !== 'yes') {
      console.log('Cancelled by user');
      await mongoose.disconnect();
      process.exit(0);
    }

    console.log('\n=== Generating Embeddings ===');

    // Get batch size from command line argument or use default
    const batchSize = parseInt(process.argv[2]) || 5;
    console.log(`Batch size: ${batchSize}`);
    console.log(`Estimated time: ${Math.ceil(documentsWithoutEmbeddings / batchSize)} batches\n`);

    // Find documents without embeddings
    const documents = await ConvertedDocument.find({
      $or: [{ embedding: { $exists: false } }, { embedding: { $size: 0 } }],
    }).select('_id title content');

    let successCount = 0;
    let errorCount = 0;
    const errors: Array<{ title: string; error: string }> = [];

    // Process in batches
    for (let i = 0; i < documents.length; i += batchSize) {
      const batch = documents.slice(i, i + batchSize);
      const batchNumber = Math.floor(i / batchSize) + 1;
      const totalBatches = Math.ceil(documents.length / batchSize);

      console.log(`\nProcessing batch ${batchNumber}/${totalBatches}...`);

      const batchPromises = batch.map(async doc => {
        try {
          await openAIService.processDocumentEmbedding((doc._id as any).toString());
          successCount++;
          console.log(`  ✓ ${doc.title}`);
        } catch (error: any) {
          errorCount++;
          const errorMessage = error.message || 'Unknown error';
          errors.push({ title: doc.title, error: errorMessage });
          console.log(`  ✗ ${doc.title}: ${errorMessage}`);
        }
      });

      await Promise.all(batchPromises);

      // Progress update
      const processed = Math.min(i + batchSize, documents.length);
      const percentage = ((processed / documents.length) * 100).toFixed(1);
      console.log(`Progress: ${processed}/${documents.length} (${percentage}%)`);

      // Add delay between batches to respect rate limits
      if (i + batchSize < documents.length) {
        console.log('Waiting 1 second before next batch...');
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }

    // Print summary
    console.log('\n=== Summary ===');
    console.log(`✓ Successfully generated: ${successCount} embeddings`);
    console.log(`✗ Failed: ${errorCount} embeddings`);

    if (errors.length > 0) {
      console.log('\n=== Errors ===');
      errors.forEach(({ title, error }) => {
        console.log(`- ${title}: ${error}`);
      });
    }

    // Verify final state
    const finalDocumentsWithEmbeddings = await ConvertedDocument.countDocuments({
      embedding: { $exists: true, $ne: [] },
    });
    console.log(`\nTotal documents with embeddings: ${finalDocumentsWithEmbeddings}/${totalDocuments}`);

    console.log('\n✓ Embedding generation complete!');
  } catch (error) {
    console.error('\n✗ Error:', error);
    process.exit(1);
  } finally {
    await mongoose.disconnect();
    console.log('\n✓ Disconnected from MongoDB');
  }
}

// Run the script
generateEmbeddings().catch(console.error);

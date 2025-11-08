"""RAG (Retrieval Augmented Generation) manager for PZ knowledge base"""

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
import os
import re


class RAGManager:
    """Manages vector database and semantic search for PZ wiki knowledge"""

    def __init__(self, persist_directory: str = "./knowledge_base"):
        """
        Initialize RAG manager

        Args:
            persist_directory: Directory to store the vector database
        """
        self.persist_directory = persist_directory

        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="pz_wiki",
            metadata={"description": "Project Zomboid wiki knowledge base"}
        )

        # Initialize embedding model (small, fast model)
        print("Loading embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Embedding model loaded")

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        Split text into overlapping chunks

        Args:
            text: Text to chunk
            chunk_size: Target size of each chunk (in characters)
            overlap: Overlap between chunks

        Returns:
            List of text chunks
        """
        # Split into paragraphs first
        paragraphs = text.split('\n\n')

        chunks = []
        current_chunk = ""

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            # If adding this paragraph would exceed chunk size
            if len(current_chunk) + len(paragraph) > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())

                # Start new chunk with overlap
                # Take last 'overlap' characters from current chunk
                overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                current_chunk = overlap_text + "\n\n" + paragraph
            else:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph

        # Add final chunk
        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def add_pages(self, pages_data: List[Dict[str, str]]) -> int:
        """
        Add wiki pages to the knowledge base

        Args:
            pages_data: List of page dictionaries with 'title', 'url', 'content'

        Returns:
            Number of chunks added
        """
        documents = []
        metadatas = []
        ids = []

        chunk_id = self.collection.count()

        print(f"Processing {len(pages_data)} pages...")

        for page in pages_data:
            title = page['title']
            url = page['url']
            content = page['content']

            # Skip very short pages
            if len(content) < 100:
                continue

            # Chunk the content
            chunks = self.chunk_text(content)

            for i, chunk in enumerate(chunks):
                documents.append(chunk)
                metadatas.append({
                    'title': title,
                    'url': url,
                    'chunk_index': i,
                    'total_chunks': len(chunks)
                })
                ids.append(f"chunk_{chunk_id}")
                chunk_id += 1

        if documents:
            print(f"Adding {len(documents)} chunks to vector database...")

            # Add to collection in batches
            batch_size = 100
            for i in range(0, len(documents), batch_size):
                batch_docs = documents[i:i+batch_size]
                batch_meta = metadatas[i:i+batch_size]
                batch_ids = ids[i:i+batch_size]

                self.collection.add(
                    documents=batch_docs,
                    metadatas=batch_meta,
                    ids=batch_ids
                )
                print(f"Added batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}")

            print(f"Successfully added {len(documents)} chunks")

        return len(documents)

    def search(self, query: str, n_results: int = 5) -> List[Dict]:
        """
        Search the knowledge base

        Args:
            query: Search query
            n_results: Number of results to return

        Returns:
            List of result dictionaries with 'content', 'metadata', 'relevance'
        """
        # Check if collection is empty
        if self.collection.count() == 0:
            return []

        # Query the collection
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )

        # Format results
        formatted_results = []

        if results['documents'] and results['documents'][0]:
            for i in range(len(results['documents'][0])):
                # Calculate relevance score (ChromaDB uses distance, lower is better)
                # Convert to similarity score (higher is better)
                distance = results['distances'][0][i]
                relevance = max(0, 1 - distance)  # Normalize to 0-1 range

                formatted_results.append({
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'relevance': relevance
                })

        return formatted_results

    def get_stats(self) -> Dict:
        """
        Get knowledge base statistics

        Returns:
            Dictionary with stats
        """
        count = self.collection.count()

        # Get unique pages
        if count > 0:
            # Sample some metadata to count unique pages
            sample_size = min(count, 1000)
            sample = self.collection.get(limit=sample_size)
            unique_titles = set()

            if sample['metadatas']:
                for metadata in sample['metadatas']:
                    unique_titles.add(metadata.get('title', 'Unknown'))

            return {
                'total_chunks': count,
                'sampled_unique_pages': len(unique_titles),
                'status': 'ready'
            }
        else:
            return {
                'total_chunks': 0,
                'sampled_unique_pages': 0,
                'status': 'empty'
            }

    def clear(self):
        """Clear the entire knowledge base"""
        self.client.delete_collection(name="pz_wiki")
        self.collection = self.client.get_or_create_collection(
            name="pz_wiki",
            metadata={"description": "Project Zomboid wiki knowledge base"}
        )
        print("Knowledge base cleared")


def build_knowledge_base(rag_manager: RAGManager, wiki_scraper, force_rebuild: bool = False):
    """
    Build the knowledge base from PZ wiki

    Args:
        rag_manager: RAG manager instance
        wiki_scraper: Wiki scraper instance
        force_rebuild: If True, clear existing data and rebuild
    """
    # Check if already populated
    stats = rag_manager.get_stats()

    if stats['total_chunks'] > 0 and not force_rebuild:
        print(f"\nKnowledge base already populated:")
        print(f"  Total chunks: {stats['total_chunks']}")
        print(f"  Sampled unique pages: {stats['sampled_unique_pages']}")
        print(f"\nUse force_rebuild=True to rebuild from scratch")
        return

    if force_rebuild:
        print("Clearing existing knowledge base...")
        rag_manager.clear()

    # Scrape wiki
    print("\nScraping PZ wiki...")
    pages_data = wiki_scraper.scrape_all()

    # Add to knowledge base
    print("\nBuilding vector database...")
    chunks_added = rag_manager.add_pages(pages_data)

    print(f"\n✅ Knowledge base built successfully!")
    print(f"   Pages scraped: {len(pages_data)}")
    print(f"   Chunks indexed: {chunks_added}")

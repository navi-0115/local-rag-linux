#!/bin/bash

echo "Starting Ollama server..."
ollama serve &  # Start Ollama in the background

echo "Ollama is ready, creating the model..."

ollama pull gemma3:4b
ollama pull nomic-embed-text
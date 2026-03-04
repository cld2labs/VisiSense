#!/bin/bash

echo "Pulling Qwen2.5-VL 7B model..."
docker exec visisense-catalogiq-ollama-1 ollama pull qwen2.5-vl:7b

echo "Model pulled successfully!"
echo "You can now use VisiSense - CatalogIQ"

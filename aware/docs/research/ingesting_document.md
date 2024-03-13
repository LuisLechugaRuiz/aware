# Ingesting document

How to ingest a document so we can use it and iterate over it to extract knowledge?

The initial idea is:

Similar algorithm than raptor - recursive summaries, but at each given time we extract the main learnings that might be relevant for the task that we are optimizing for. So instead of summaries we record the "extractions" as we are sending a task that need to be optimized. This way we are modifying the kind of storing that we will perform.

But the concept remain relevant, the recursive summaries might be relevant to increase the connections between different parts of the documents.

## Considerations

Some models will have huge context windows soon. It might make sense to just send them directly the specific document and obtain someone the relevant info instead of chunking the document.
AN AI TO IMPROVE SCIENTIFIC KNOWLDGE

TOOLS:

- Arxviz. (To find info related on arxviz):
    - Service: 
        - Request:
            - find info on arxviz (str)
        - Response:
            - List of content (List Content)
                - Content
                    - Content (str)
                    - Source (str)
- Search internet. (To find info in the web about specific topic)
- Save theory - (File writing along a database to save position and insert - edit existing knowledge).
- Leader. (ORCHESTRATOR)

With this simple agents we can create a complex use-case.

Lets start simple and make it effective. If the AI is not only able to answer to user, but more importantly to find a good paper about a specific knowledge, then it will be ready.

—-
Idea:

Save theory will have instructions to be written as a paper with best practices about how to create papers and all the edits.

This way the thought process will optimize for this task and be able to instrospect the paper as part of his tools.

This means: MEMORY ADAPTER - to the paper itself, the database that contains the knowledge about the paper.

—-
Which is the entry?

Is the event from user. A request to write a paper about a specific topic and the possibility to interact with the AI on real-time to notify important details.

So a topic to stream updates about the task is important.

Lets first just be the event of user message and then the team leader requesting to the agents what to do.

There is a coordinator that administrates task execution inside the system even when different agents are connected.

The orchestrator ensure proper behavior of components.


--
### TODO:

fix file and move it to use-cases.

### Agents structure

Manager (Orchestrator)
  Clients:
    - create_paper.
    - make_modifications.

Author (FileCreator)
 Services:
   - create_paper.
   - make_modifications.
 Clients:
   - search_info.

Researcher (ArXivExplorer)
   - search_info.


### ArXivExplorer

PROFILE NEEDS CAPABILITIES.

In order to MAINTAIN a specific profile for each agent.

This will be very detailed. We need to have capabilities that are able to have the best profile.

—-
ARXIV 

Capability have a way to add databases to memory.

This way thought later can use a tool to find specific info.

Imagine a:

add_paper(name) - this function calls add document which internally creates a database for that specific paper.

Then our thought generator gets a new document inserted to search on it with:

search_document (document name, queries) - this function search specific info on a paper.

—-
More functions:

get_papers(query) - this function searches by similarity on ArXiV and returns the abstract of the papers so we can use them in the future.

---
what if agents can share documents with each other??

this way our Author can also have access to the papers and add them so he can iterate over thems to get answers.

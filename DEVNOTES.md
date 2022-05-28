# Introduction
A typical note taking app has a collection of notebooks, each notebook has pages and each page contains the actual content.
For reference, this is similar to Evernote and OneNote. Google Keep doesn't have a notebooks, there are only pages.

A note taking app involves lots of write and update operations. Often, the client calls the server within a second the user makes changes.

# Implementations

## Simple Replace
In the most simplest implementation, the client sends the whole page content as one long string to the server everytime the user does any kind of change - add new text, modify or delete text, etc. The server simply replaces the existing data in the database with the latest client data.
This is how Google Keep seems to handle plain text notes.  
The downside of this approach is visible when thousands of users simultaneously update their pages containing large amount of content. This increases the ingress network traffic and writes on the db take more time due to larger data size.

(Apart from the performance and n/w issues there could be other reasons that I am unable to identify now.)

## Array of Nodes
Instead of treating the whole page as a single string we can break down the content into nodes of different types:
 - Headers - Page title, H1, H2, H3
 - Paragraphs - Text paragraphs, Code blocks, Block quotes
 - Lists - Ordered/unordered lists, To-Do list, Checkboxes
 - Photo
 - Table

Since all the elements are in sequential order, the page can be considered as an array of nodes. Each node is composed of metadata and the actual content.  
_Note:_ OneNote allows adding nodes anywhere on the page. I personally find that less useful and more clumsy and for the scope of this project, we are ignoring such an arrangement.

Whenever the text corresponding to a node is updated on the client side, only that node's metadata + content is sent to the server and server will replace the existing node content with the latest.

This is how Evernote and OneNote seem to handle page updates. Even Google Keep uses this approach for handling Checkboxes.

# Dev Plan
1. Start with "Simple Replace" implementation
2. Write a tool to benchmark performance.
3. Update the code with "Array of Nodes" implementation
4. Update the tool to benchmark the new implementation

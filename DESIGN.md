THis repo will be used as a personal knowlegde base, i will add articles, notes, tasks, projects and so on, and i expect a personalized AI agent to assist me in keeping the knowlegdebase updated, connected and trimmed.

I also want to ask questions via AI agents to get data from the knowlegdebase, that is customized to my questions WHILE we ensure that we provide links to the pages we are getting data from.

This should hopefully work completly through the terminal / AI tools like Claude.

All of this requires that we are VERY good at updating pages with relevant tags, properties and links. I would like for us to make a standard template for properties, and i want a definition of the tags we are allowed to use. The tags list should be lean, but we should still be able to expand it dynamicly by the AI if needed. The properties NEEDS to contain a small summary of what the page contains as it is used for searching for things.

There should be some different workflows i could use.

1. Put data in inbox

- Data put in inbox would be read and a corresponding page created for this data. (This should follow a atomic note) with links to relevant data
- use obsidian CLI to search for related pages that we would need to link this page up with. (obsidian search query="Query goes here", tag name="tag goes here"
- A new file is created in inbox for desitions that are required from me.

2. In a AI bot i ask for information

- The AI makes relevant searches using obsidian search query="query" "query 2"
- For each page returned read the property description and detirmane if its relevant for the query (obsidian property:read file="path/to/file.md" name=description
- Answer question with references to files this data comes from.

This will need to be expanded in the future. Anything that can be solved with small scripts (Bash or Python) is good this way we can offload some of the thinking from AI to local hardware.

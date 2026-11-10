/**
 * dashboard.js - Load papers from REST API display on dashboard.
 */

async function loadPapers() {
    const list = document.getElementById("paper-list");
  
    try {
      const response = await fetch("/api/papers");   // send GET /api/papers
      if (!response.ok) {                             // anything other than 2xx
        throw new Error("Request failed (" + response.status + ")");
      }
      const data = await response.json();             // turn the JSON text into an object
  
      list.innerHTML = "";                      
      for (const paper of data.items) {
        list.appendChild(paperItem(paper));
      }
    } catch (error) {
      list.innerHTML = "<li>Couldn't load papers: " + error.message + "</li>";
    }
  }
  
  // Build one <li> for a paper.
  function paperItem(paper) {
    const li = document.createElement("li");
  
    const title = document.createElement("strong");
    title.textContent = paper.title;
  
    const details = document.createElement("div");
    details.textContent =
      paper.authors.join(", ") + " · " + paper.venue + " · " + paper.year +
      " · Cited by " + paper.citations.toLocaleString();
  
    li.appendChild(title);
    li.appendChild(details);
    return li;
  }
  
  // Run once the page has loaded.
  loadPapers();
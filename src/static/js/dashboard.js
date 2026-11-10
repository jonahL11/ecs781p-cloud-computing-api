/**
 * dashboard.js - Load papers from REST API display on dashboard.
 */

async function loadPapers(query = "") {
    const list = document.getElementById("paper-list");
  
    try {
      // e.g. "/api/papers?q=cloud". URLSearchParams safely encodes spaces and symbols.
      const url = "/api/papers?" + new URLSearchParams({ q: query });
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error("Request failed (" + response.status + ")");
      }
      const data = await response.json();
  
      list.innerHTML = "";
      if (data.items.length === 0) {
        list.innerHTML = '<li class="empty">No papers match your search.</li>';
        return;
      }
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
    li.className = "paper";

    const title = document.createElement("strong");
    title.className = "paper-title";
    title.textContent = paper.title;
  
    const details = document.createElement("div");
    details.className = "paper-meta";
    details.textContent =
      paper.authors.join(", ") + " · " + paper.venue + " · " + paper.year +
      " · Cited by " + paper.citations.toLocaleString();
  
    li.appendChild(title);
    li.appendChild(details);
    return li;
  }

  function debounce(fn, ms = 300) {
    let timer;
    return (...args) => {
      clearTimeout(timer);
      timer = setTimeout(() => fn(...args), ms);
    };
  }
  
// Search as the user types
const searchInput = document.getElementById("search-input");
searchInput.addEventListener("input", debounce(() => {
  loadPapers(searchInput.value.trim());
}));

// Load all papers
loadPapers();
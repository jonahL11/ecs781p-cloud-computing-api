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
      [paper.authors.join(", "), paper.venue, paper.year].filter(Boolean).join(" · ") +
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
  
const searchInput = document.getElementById("search-input");
searchInput.addEventListener("input", debounce(() => {
  loadPapers(searchInput.value.trim());
}));

const modal = document.getElementById("paper-modal");
const form = document.getElementById("paper-form");
const formError = document.getElementById("form-error");

document.getElementById("add-paper-btn").addEventListener("click", () => {
  form.reset();                // clear anything typed last time
  formError.textContent = "";  // clear old error messages
  modal.showModal();
});

document.getElementById("cancel-btn").addEventListener("click", () => modal.close());

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const body = Object.fromEntries(new FormData(form));

  try {
    const response = await fetch("/api/papers", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await response.json();

    if (response.status !== 201) {
      formError.textContent = data.error;
      return;
    }
    modal.close();
    loadPapers(searchInput.value.trim());
  } catch (error) {
    formError.textContent = "Couldn't save: " + error.message;
  }
});


// Load all papers
loadPapers();

async function loadServerInfo() {
  try {
    const response = await fetch("/api/health");
    const data = await response.json();
    document.getElementById("served-by").textContent = data.served_by;
  } catch (error) {
    document.getElementById("served-by").textContent = "unknown";
  }
}
loadServerInfo();

// Sidebar
const sidebar = document.getElementById("sidebar");
const overlay = document.getElementById("overlay");

function openSidebar() {
  sidebar.classList.add("open"); 
  overlay.classList.add("show");    
}

function closeSidebar() {
  sidebar.classList.remove("open");
  overlay.classList.remove("show");
}

document.getElementById("menu-btn").addEventListener("click", openSidebar);
overlay.addEventListener("click", closeSidebar);   // click outside to close

// Press Esc to close
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") closeSidebar();
});

const panels = {
  all: document.getElementById("papers-panel"),
  library: document.getElementById("library-panel"),
  discover: document.getElementById("discover-panel"),
};

function showView(view) {
  for (const name in panels) {
    panels[name].classList.toggle("hidden", name !== view);
  }

  document.querySelectorAll(".nav-item").forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.view === view);
  });

  const onAll = view === "all";
  document.getElementById("search-input").classList.toggle("hidden", !onAll);
  document.getElementById("add-paper-btn").classList.toggle("hidden", !onAll);

  closeSidebar();
}

document.querySelectorAll(".nav-item").forEach((tab) => {
  tab.addEventListener("click", () => showView(tab.dataset.view));
});
function scrollToTop() {
  window.scrollTo({
    top: 0,
    behavior: 'smooth'
  });
}

function scrollToBottom() {
  window.scrollTo({
    top: document.body.scrollHeight,
    behavior: 'smooth'
  });
}

const url = new URL(window.location.href);

const params = new URLSearchParams(url.search);

const ip = params.get('ip');

function submitForm() {
  var form = document.getElementById('form');

  if (form) {
    form.submit();
  } else {
    console.error('Form with ID "form" not found.');
  }
}

function getBaseUrl(url) {
  // Create a new URL object with the given URL
  const urlObject = new URL(url);
  // Extract and return the hostname (base URL without path)
  return urlObject.hostname;
}


function ipVal() {
  const url = new URL(window.location.href);

  const params = new URLSearchParams(url.search);

  const ip = params.get('ip');
  document.getElementById("ip").value = ip;
  var newDiv = document.createElement('div');

  newDiv.innerHTML = `
      <div class="container">
        <span class="loading loading-spinner text-primary" style="width: 2.5rem; z-index: 2;"></span>
      </div>
  `;
  
  document.body.appendChild(newDiv);
  scrollToBottom()
  submitForm()
}

function authLAN() {
  const links = document.querySelectorAll('a.lanFiles');

  if (links.length > 0) {
    links.forEach(link => {
      let currentHref = link.getAttribute('href');

      let newHref = `${currentHref}?ip=${ip}`;
      link.setAttribute('href', newHref);
    });
  } else {
    console.error('No links found.');
  }
}

function initialize() {
  document.getElementById("currUrl").innerHTML = getBaseUrl(window.location.href);

  authLAN()
}
document.addEventListener('DOMContentLoaded', initialize);
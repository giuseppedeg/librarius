
let subnav_content = document.getElementById("subnav-content-documents");
let subnav_content_small = document.getElementById("subnav-small-content-documents");

for (i = 0; i < all_documents.length; ++i) {
    let a = document.createElement('a');
    a.setAttribute('href','#');
    a.setAttribute('onclick','load_document("'+all_documents[i]+'")');
    a.innerText = "Page "+ all_documents[i];
    subnav_content.appendChild(a);

    let li = document.createElement('li');
    li.classList.add("u-nav-item");
    let a2 = document.createElement('a');
    a2.classList.add("u-button-style");
    a2.classList.add("u-nav-link");
    a2.setAttribute('href','#');
    a2.setAttribute('onclick','load_document("'+all_documents[i]+'")');
    a2.innerText = "Page "+ all_documents[i];
    li.appendChild(a2);
    subnav_content_small.appendChild(li);

}
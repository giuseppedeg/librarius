function load_all_docs(){
    let subnav_content = document.getElementById("subnav-content-documents-list");
    let subnav_content_small = document.getElementById("subnav-small-content-documents");
    
    subnav_content.innerHTML = ""

    for (i = 0; i < all_documents.length; ++i) {
        let div = document.createElement('div');
        div.classList.add("docs-in-menu");

        let a = document.createElement('a');
        a.classList.add("link-to-doc");
        a.setAttribute('href','#');
        a.setAttribute('onclick','load_document("'+all_documents[i]+'")');
        a.innerText = all_documents[i];

        let but = document.createElement('button');
        but.classList.add("button-delete-doc");
        but.setAttribute('onclick','deleteImage_ask("'+all_documents[i]+'")');
        but.innerText = "Delete"

        div.appendChild(a);
        div.appendChild(but);

        subnav_content.appendChild(div);

        // let li = document.createElement('li');
        // li.classList.add("u-nav-item");
        // let a2 = document.createElement('a');
        // a2.classList.add("u-button-style");
        // a2.classList.add("u-nav-link");
        // a2.setAttribute('href','#');
        // a2.setAttribute('onclick','load_document("'+all_documents[i]+'")');
        // a2.innerText = "Page "+ all_documents[i];
        // li.appendChild(a2);
        // subnav_content_small.appendChild(li);

    }
};

function load_all_models(){
    let select_ls_model = document.getElementById("select-ls-model")

    for (i = 0; i < all_ls_models.length; ++i) {
        let curr_model_path = all_ls_models[i];
        let curr_model_name = curr_model_path.replace(/^.*[\\/]/, '');

        let opt = document.createElement('option');
        opt.innerHTML = curr_model_name
        opt.value = curr_model_path

        select_ls_model.appendChild(opt);
    }

    let select_htr_model = document.getElementById("select-HTR-model")
    for (i = 0; i < all_trocr_models.length; ++i) {
        let curr_model_path = all_trocr_models[i];
        let curr_model_name = curr_model_path.replace(/^.*[\\/]/, '');

        let opt = document.createElement('option');
        opt.innerHTML = curr_model_name
        opt.value = curr_model_path

        select_htr_model.appendChild(opt);
    }

}

load_all_docs();
load_all_models()
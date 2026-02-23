//var all_keywords = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]

var max_transcripts_options = 20
var MAX_ELEM_IN_LIST_INPUT = 10

/* Filtra la lista di keyword sulla destra in base alle lettere inserite nel campo di testo*/
function filter_list() {
    var input; 
    var filtro;
    var inscreen_keywords;
    var i;
    var text;

    input = document.getElementById("text_input");
    filtro = input.value.toUpperCase();
    inscreen_keywords = document.getElementById("keyword_list");
    
    $(inscreen_keywords).empty();

    var max_iter = all_keywords.length
    if (max_iter > max_transcripts_options)
        max_iter = max_transcripts_options

    for (i = 0; i < max_iter; i++) {
       
        text = all_keywords[i]
        
        if (text.toUpperCase().indexOf(filtro) > -1) {
            $("<li onclick=\"select_transcript('"+text+"')\">"+text+"</li>").appendTo(inscreen_keywords)
        }
   }
}

// Autocomplete -------------------------------------------------------------------------

/* La funzione crea la lista di opzioni visibile sotto il textbox con le trascrizioni per l'autocompletamento 
La funzione prende come parametro un elemento di input e una lista di opzioni*/
function autocomplete(inp, arr) {

    var currentFocus;
    
    
    /*execute a function when someone writes in the text field:*/
    inp.addEventListener("input", function(e) {
        var a, b, i, val = this.value;

        closeAllLists();
        if (!val) 
            return false;

        currentFocus = -1;
        
        /*Creiamo in DIV che contiene tutti i valori da mostrare nella lista. è il Cntainer*/
        a = document.createElement("DIV");
        a.setAttribute("id", this.id + "autocomplete-list");
        a.setAttribute("class", "autocomplete-items");
       
        this.parentNode.appendChild(a);

        // filtriamo la lista tenendo conto delle lettere inserite nel textfield
        let matched_elems = 0
        for (i = 0; i < arr.length; i++) {
          if (matched_elems <= MAX_ELEM_IN_LIST_INPUT  && arr[i].substr(0, val.length).toUpperCase() == val.toUpperCase()) {
            // Creiamo un DIV per ogni elemento che matcha
            b = document.createElement("DIV");
            b.innerHTML = "<strong>" + arr[i].substr(0, val.length) + "</strong>";
            b.innerHTML += arr[i].substr(val.length);
            b.innerHTML += "<input type='hidden' value='" + arr[i] + "'>";

            // AL CLICK dell'opzione dovrei inviare la trascrizione -----------------------------------<
            b.addEventListener("click", function(e) {
                //inp.value = this.getElementsByTagName("input")[0].value;
                select_transcript(this.getElementsByTagName("input")[0].value)
                closeAllLists();
            });
            a.appendChild(b);
            matched_elems = matched_elems + 1;
          }
        }
    });

    // Controlli della tastiera - UP, DOWN, ENTER, TAB
    inp.addEventListener("keydown", function(e) {
        var x = document.getElementById(this.id + "autocomplete-list");
        if (x) x = x.getElementsByTagName("div");
        
        if (e.keyCode == 9) { //DOWN
          e.preventDefault();
          currentFocus++;
          addActive(x);
        } else if (e.keyCode == 38) { //UP
          currentFocus--;
          addActive(x);
        } else if (e.keyCode==13) { //TAB
          e.preventDefault();
          if (currentFocus > -1) {
            if (x) x[currentFocus].click();
          }else{
            document.getElementById("ok_transc_btn").click()
          }
        }

        /*else if (e.keyCode == 13) { //ENTER  --- invia?=?
            e.preventDefault();
            if (currentFocus > -1) {
                if (x) x[currentFocus].click();
            }
        }*/
    });

    // LA funzione evidenzia l'item attivo
    function addActive(x) {
      if (!x) return false;
      removeActive(x);
      if (currentFocus >= x.length) currentFocus = 0;
      if (currentFocus < 0) currentFocus = (x.length - 1);
      x[currentFocus].classList.add("autocomplete-active");
    }
    // Rimuove l'item da attivo
    function removeActive(x) {
      for (var i = 0; i < x.length; i++) {
        x[i].classList.remove("autocomplete-active");
      }
    }

    // Chiudere la lista
    function closeAllLists(elmnt) {
      var x = document.getElementsByClassName("autocomplete-items");
      for (var i = 0; i < x.length; i++) {
        if (elmnt != x[i] && elmnt != inp) {
          x[i].parentNode.removeChild(x[i]);
        }
      }
    }

    /*execute a function when someone clicks in the document:*/
    document.addEventListener("click", function (e) {
        closeAllLists(e.target);
    });
}
  

// Associamo la funzione per l'autocompletamento al textfield
autocomplete(document.getElementById("text_input"), all_keywords);
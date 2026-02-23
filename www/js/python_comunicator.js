function load_document(doc){
    eel.load_document(doc)

    document.getElementById('delete-tool').setAttribute("style","pointer-events:all;opacity: 1");
    document.getElementById('correct-tool').setAttribute("style","pointer-events:all;opacity: 1");
    document.getElementById('clear-tool').setAttribute("style","pointer-events:all;opacity: 1");
    document.getElementById('transcribe-tool').setAttribute("style","pointer-events:all;opacity: 1");
    document.getElementById('apply-trans-tool').setAttribute("style","pointer-events:all;opacity: 1");

    
}

function next_word(){
    const transcript = document.getElementById("text_input").value

    console.log(transcript)

    if (transcript.length>0){

        //transcript.value = ""
        //$("#text_input").focus();

        console.log("SEND")
        eel.set_current_word_transcription(transcript, "NEXT")
    }

    eel.next_word()
}

function prev_word(){
    eel.prev_word()
}

function click_on_transcript(r_id, w_id){
    eel.to_word(w_id, r_id)
}

function delete_current_word_ask(){
    document.getElementById('modal-del-word').style.display='block'
    document.getElementById('text_input').blur();
}

function delete_current_word(){
    eel.delete_current_word()
    document.getElementById('modal-del-word').style.display='none'
}

function clear_transcripts_ask(){
    document.getElementById('modal-del-cleartrans').style.display='block'
    document.getElementById('text_input').blur();
}

function clear_transcripts(){
    eel.clear_transcripts()
    document.getElementById('modal-del-cleartrans').style.display='none'
}

function transcribe(){
    let htr_model_select = document.getElementById('select-HTR-model');
    let htr_model = htr_model_select.options[htr_model_select.selectedIndex].value;

    let num_options = document.getElementById('select-num-options').value;

    let language_select = document.getElementById('select-language');
    let language = language_select.options[language_select.selectedIndex].value;

    show_modal_create_trans()

    eel.transcribe(htr_model, num_options, language)

    // hide_modal_create_trans()
}

function apply_transcription_ask(){
    document.getElementById('modal-apply-trans').style.display='block'
    document.getElementById('text_input').blur();
}

function apply_transcription(){
    eel.apply_transcription()
    document.getElementById('modal-apply-trans').style.display='none'
}


function correct_segmentation(){
    eel.correct_segmentation()
}



function select_transcript(transcript, ind){
    var text_input = document.getElementById("text_input")

    text_input.value = ""
    $("#text_input").focus();

    eel.set_current_word_transcription(transcript, "LIST_"+ind)
    eel.next_word()

}

function send_transcript_by_ok(mode){
    //var transcript_area = document.getElementById("transcript_textarea")
    var transcript = document.getElementById("text_input")
    

    //var full_transcript = transcript_area.innerHTML
    var word = transcript.value

    if (word.length>0){
        //full_transcript = full_transcript + " " + word
        //full_transcript = full_transcript.trimStart()
        
        //transcript_area.innerHTML = full_transcript

        transcript.value = ""
        $("#text_input").focus();

        //console.log(full_transcript)
        //eel.set_current_line_transcription(full_transcript)
        eel.set_current_word_transcription(word, mode)
        eel.next_word()
    }
}

eel.expose(show_transcripts_list)
function show_transcripts_list(transcripts_list){
    var inscreen_keywords = document.getElementById("keyword_list");
    $(inscreen_keywords).empty();

    var max_iter = transcripts_list.length
    if (max_iter > max_transcripts_options)
        max_iter = max_transcripts_options

    for (i=0; i<max_iter; i++) {
        text = transcripts_list[i]
        $("<li onclick=\"select_transcript('"+text+"', '"+(i+1)+"')\">"+text+"</li>").appendTo(inscreen_keywords)
   }
}


eel.expose(update_transcription_area)
function update_transcription_area(transcription){
    var transcript_area = document.getElementById("transcript_textarea");
    transcript_area.innerHTML = transcription
}

eel.expose(update_transcript_input)
function update_transcript_input(transcript){
    var text_input = document.getElementById("text_input");

    text_input.value = transcript
    $("#text_input").focus();
}


eel.expose(show_current_word_img)
function show_current_word_img(img_path){
    var timestamp = new Date().getTime();
    document.getElementById("img_word").src=img_path+"?t="+timestamp;

    //set_focus_on_textinput();
    window.new_transcriptiKCon = true;
}

eel.expose(show_current_line_img)
function show_current_line_img(img_path){
    var timestamp = new Date().getTime();
    document.getElementById("img_row").src=img_path+"?t="+timestamp;
}

function set_focus_on_textinput(){
    text_input = document.getElementById("text_input");
    text_input.focus();
    text_input.select();
}

function start_instert_transcription(){
    const text_input = document.getElementById("text_input");

    const action_on_field = () => {
        console.log("STOP Thinking Time")
        eel.stop_thinking_timer();
    };

    // intercept input in text field to stop thinking time
    text_input.addEventListener('input', action_on_field);

    // intercept click in text field to stop thinking time
    text_input.addEventListener('click', action_on_field);

    // intercept cursor movement (arrows) in text field to stop thinking time
    text_input.addEventListener('keydown', function(e) {

        const keys = ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Home', 'End', 'Control', 'Shift', 'Meta'];

        if (keys.includes(e.key) && !e.altKey) {
            action_on_field();
        }
    });
};

function uploadImage(){
    show_modal_load_document();
    let ls_model_select = document.getElementById('select-ls-model');
    let ls_model = ls_model_select.options[ls_model_select.selectedIndex].value;

    eel.uploadImage(ls_model) (r => {
        all_documents[all_documents.length]=r;
        load_all_docs();
    });

};

function deleteImage_ask(id_img){
    document.getElementById('id-img-to-delete').innerHTML=id_img
    document.getElementById('modal-del-doc').style.display='block'
    document.getElementById('text_input').blur();
}

function deleteImage(){
    id_img = document.getElementById('id-img-to-delete').innerHTML

    eel.deleteImage(id_img)
    document.getElementById('modal-del-doc').style.display='none'
    
    document.getElementById('img_row').src="images/row_example.png";
    document.getElementById('img_word').src="images/word_example.png";
    document.getElementById('transcript_textarea').innerHTML="";


    const index = all_documents.indexOf(id_img);
    if (index > -1) { 
        all_documents.splice(index, 1); 
    }
    
    load_all_docs()

}

function load_home(){
    eel.release_document();

    document.getElementById('img_row').src="images/row_example.png";
    document.getElementById('img_word').src="images/word_example.png";
    document.getElementById('transcript_textarea').innerHTML="";
    text_input.value = ""
    $("#text_input").focus();
    
    show_transcripts_list(["","","","",""])


    document.getElementById('delete-tool').setAttribute("style","pointer-events:none;opacity: 0.3");
    document.getElementById('correct-tool').setAttribute("style","pointer-events:none;opacity: 0.3");
    document.getElementById('clear-tool').setAttribute("style","pointer-events:none;opacity: 0.3");
    document.getElementById('transcribe-tool').setAttribute("style","pointer-events:none;opacity: 0.3");
    document.getElementById('apply-trans-tool').setAttribute("style","pointer-events:none;opacity: 0.3");

    document.getElementById('ok_transc_btn').disabled = true; 
    
    
}


// MADALS AND TIMER --------------
var seconds = 0;
var minutes = 0;

var Interval;

eel.expose(show_modal_load_document)
function show_modal_load_document(){
    document.getElementById('modal-load-document').style.display='block'

    clearInterval(Interval);
    Interval = setInterval(startTimer, 1000);

}

eel.expose(hide_modal_load_document)
function hide_modal_load_document(){
    clearInterval(Interval);
    seconds = 0;
    minutes = 0;
    appendSeconds = document.querySelectorAll('.seconds');
    appendMinutes = document.querySelectorAll('.minutes');
    appendSeconds.forEach(element => {
        element.innerHTML = "00";
    });
    appendMinutes.forEach(element => {
        element.innerHTML = "00";
    });
    document.getElementById('modal-load-document').style.display='none';
}

eel.expose(show_modal_create_trans)
function show_modal_create_trans(){
    document.getElementById('modal-create-transcripts').style.display='block'

    clearInterval(Interval);
    Interval = setInterval(startTimer, 1000);

}

eel.expose(hide_modal_create_trans)
function hide_modal_create_trans(){
    clearInterval(Interval);
    seconds = 0;
    minutes = 0;
    appendSeconds = document.querySelectorAll('.seconds');
    appendMinutes = document.querySelectorAll('.minutes');
    appendSeconds.forEach(element => {
        element.innerHTML = "00";
    });
    appendMinutes.forEach(element => {
        element.innerHTML = "00";
    });
    document.getElementById('modal-create-transcripts').style.display='none';
}


function startTimer () {
    var appendMinutes = document.querySelectorAll('.minutes');
    var appendSeconds = document.querySelectorAll('.seconds');
    // var appendSeconds = document.getElementsByClassName("seconds");

    seconds++;
    
    if(seconds <= 9){
        appendSeconds.forEach(element => {
            element.innerHTML = "0" + seconds;
        });
    }
    
    if (seconds > 9){
        appendSeconds.forEach(element => {
            element.innerHTML = seconds;
        });
    }
  
    if (seconds > 59) {
      minutes++;
      appendMinutes.forEach(element => {
        element.innerHTML = "0" + minutes;
      });
      seconds = 0;
      appendSeconds.forEach(element => {
        element.innerHTML = "0" + 0;
      });
    }
    if (minutes > 9){
      appendMinutes.forEach(element => {
        element.innerHTML = minutes;
      });
      
    }
}


function _test(){

    let ls_model_select = document.getElementById('select-ls-model');
    let ls_model = ls_model_select.options[ls_model_select.selectedIndex].value;

    let htr_model_select = document.getElementById('select-HTR-model');
    let htr_model = htr_model_select.options[htr_model_select.selectedIndex].value;

    let num_options = document.getElementById('select-num-options').value;
    

    

    console.log("LS MODEL: "+ls_model)
    console.log("HTR MODEL: "+htr_model)
    console.log("N OPTIONS: "+num_options)
}

document.addEventListener('keydown', function(event) {
    const activeModal = Array.from(document.querySelectorAll('.modal'))
                                      .find(m => m.style.display === 'block');

    if (!activeModal) {
        if(event.altKey && event.key == "ArrowLeft") {
            //alert('Left was pressed');
            prev_word();
        }
        else if(event.altKey && event.key == "ArrowRight") {
            next_word();
        }

        else if(event.altKey && event.key == "Delete"){
            delete_current_word_ask()
        }
    }
});



$(document).ready(function(){

    // UPLOAD CLASS DEFINITION
    // ======================

    var dropZone = document.getElementById('music-drop-zone');
    var uploadForm = document.getElementById('js-music-upload-form');

    var startUpload = function(files) {
        console.log(files);
        let url = "/music-file-upload";
        let formData = new FormData();
      
        var i;
        for (i = 0; i < files.length; i++) {
            let formData = new FormData();
            formData.append('file', files[i]);
            fetch(url, {
            method: 'POST',
            body: formData
            })
            .then(() => { console.log("file upload error")})
            .catch(() => { console.log("file upload error") })
        }
      }       
    

    uploadForm.addEventListener('submit', function(e) {
        var uploadFiles = document.getElementById('js-music-upload-files').files;
        e.preventDefault()

        startUpload(uploadFiles)
    })

    dropZone.ondrop = function(e) {
        e.preventDefault();
        this.className = 'upload-music-drop-zone';

        startUpload(e.dataTransfer.files)
    }

    dropZone.ondragover = function() {
        this.className = 'upload-music-drop-zone drop';
        return false;
    }

    dropZone.ondragleave = function() {
        this.className = 'upload-music-drop-zone';
        return false;
    }
});

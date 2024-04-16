$(document).ready(function () {
    $('#name').on('input', function() {
        var nameValue = $(this).val();
        var urlPathValue = nameValue.replace(/\./g, '/');
        $('#url_path').val("/"+urlPathValue);
        var replacedValue = nameValue.replace(/\./g, ' ');
        var capitalizedWords = replacedValue.toLowerCase().replace(/\b\w/g, function(char) {
            return char.toUpperCase();
        });
        $('#title').val(capitalizedWords);
    });
});
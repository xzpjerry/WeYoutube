$("#enterbtn").click(function() {
    $("#enterForm").show();
    $("#createForm").hide();
  })
$("#createbtn").click(function() {
    $("#createForm").show();
    $("#enterForm").hide();
})

$("#enterForm").submit(function(e) {
    e.preventDefault(); // avoid to execute the actual submit of the form.

    var form = $(this);
    var url = form.attr('action');

    $.ajax({
          type: "POST",
          url: url,
          data: form.serialize(),
          success: function()
          {
            window.location.href = "/watch";
          },
          error: function(xhr){
            var error = JSON.parse(xhr.responseText);
            alert(error['errors']);
          }
        });
});

$("#createForm").submit(function(e) {
    e.preventDefault();

    var form = $(this);
    var url = form.attr('action');

    $.ajax({
          type: "POST",
          url: url,
          data: form.serialize(),
          success: function()
          {
            window.location.href = "/watch";
          },
          error: function(xhr){
            var error = JSON.parse(xhr.responseText);
            alert(error['errors']);
          }
        });
});
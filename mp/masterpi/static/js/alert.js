function showAlert(type, msg) {
  if (type == 'success') {
    style = 'success';
    heading = 'Success';
  } else {
    style = 'danger';
    heading = 'Warning';
  }

  $('#msg').animate({
    height: '+=72px'
  }, 300);

  $('<div class="alert alert-' + style + '">' +
    '<strong>[' + heading + ']</strong> ' + msg +
    '</div>').hide().appendTo('#msg').fadeIn(1000);

  $('.alert').delay(3000).fadeOut('normal', function() {
    $(this).remove();
  });

  $('#msg').delay(4000).animate({
    height: '-=72px'
  }, 300);
}

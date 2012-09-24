$(function () {
      $('.repo').each(function (idx, el) {
                          var user = $(el).attr('data-user'), name = $(el).attr('data-name');
                          $(el).repo({user:user, name:name}).css('height', '100%');
                      });
  });

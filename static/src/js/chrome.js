openerp.doctor = function(instance) {

  // Override the set_title method to our own to have recognizable document titles
  // FIXME: this comes *after* it has already been set to OpenERP earlier, perhaps no biggie
  instance.web.WebClient.include({
    set_title: function(title) {
      title = _.str.clean(title);
      var sep = _.isEmpty(title) ? '' : ' - ';
      document.title = title + sep + 'ClinicaDigital';
    },
  });


}

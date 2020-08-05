$(document).ready(function () {
    $(document).on('click', '.toggle-description', function (e) {
        e.preventDefault();
        if ($(this).hasClass('hide')) {
            $(this).closest('.abstract-container').find('.long').hide();
            $(this).closest('.abstract-container').find('.dots').show();
            $(this).parent().find('.toggle-description.show').show();
            $(this).hide();
        } else {
            $(this).closest('.abstract-container').find('.dots').hide();
            $(this).closest('.abstract-container').find('.long').fadeIn();
            $(this).parent().find('.toggle-description.hide').show();
            $(this).hide();
        }
    });

    $(document).on('click', '.show-authors', function (e) {
        e.preventDefault();
        $(this).parent().find('.author.d-none').removeClass('d-none');
        $(this).parent().find('.remove-on-show-authors').remove();
        $(this).remove();
    });
});
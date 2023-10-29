(function ($) {
    "use strict"

/*******************
Sweet-alert JS
*******************/

    }, document.querySelector(".sweet-success").onclick = function () {
        swal("Operation Successful !!", "Miner's honesty has been updated !!", "success")
        .then((value) => {
            if (value) {
                location.reload();
            }
        });
});

(jQuery);

"use strict"
document.querySelector(".sweet-success").onclick = function () {
        swal("Operation Successful !!", "Miner has been updated !!", "success")
        .then((value) => {
            if (value) {
                location.reload();
            }
        });
}
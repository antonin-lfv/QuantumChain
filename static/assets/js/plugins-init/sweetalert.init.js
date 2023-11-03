"use strict"
document.querySelector(".sweet-success-honest").onclick = function () {
        swal("Operation Successful !!", "Miner's honesty has been updated !!", "success")
        .then((value) => {
            if (value) {
                location.reload();
            }
        });
}

document.querySelector(".sweet-success-active").onclick = function () {
        swal("Operation Successful !!", "Miner's activity has been updated !!", "success")
        .then((value) => {
            if (value) {
                location.reload();
            }
        });
}
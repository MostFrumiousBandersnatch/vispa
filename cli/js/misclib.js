const MISC_LIB = (function () {
    'use strict';

    var lib = {};

    lib.btnClickPromise = (btn, action) => {
        // dirty hack to prevent outdated promises from attempts to resolve
        var dsKey = '__cnt_' + action,
        cnt = Number(btn.dataset[dsKey] || 0) + 1 
        btn.dataset[dsKey] = cnt;

        return new Promise((resolve, reject) => {
            function handler (e) {
                e.preventDefault();
                btn.removeEventListener('click', handler);

                if (btn.dataset[dsKey] !== String(cnt)) {
                    console.log('this promise is totally hopeless');
                    reject();
                    return;                
                }

                resolve(action);
            };

            btn.addEventListener('click', handler);
        });
    };
    
    return lib;
})();


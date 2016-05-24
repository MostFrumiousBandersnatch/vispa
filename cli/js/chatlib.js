const CHAT_LIB = (function () {
    'use strict';

    var lib = {}, _pr_cache = {};

    const TOKEN_STORAGE = 'chat_jwt';
    
    lib.saveSession = (token) => {
        window.sessionStorage[TOKEN_STORAGE] = token;
    };

    lib.clearSession = () => {
        delete window.sessionStorage[TOKEN_STORAGE];
    };

    lib.restoreSession = () => {
        return new Promise((resolve, reject) => {
            var stored = window.sessionStorage[TOKEN_STORAGE],
                parsed,
                curr_ts;
            
            if (stored) {
                try {
                    parsed = JSON.parse(atob(stored.split('.')[1]));                
                } catch (e) {
                    return reject('token found but incorrect');
                }

                curr_ts = Math.floor(Date.now() / 1000);

                if (parsed.exp > curr_ts) {
                    resolve({
                        username: parsed.name,
                        token: stored
                    });
                } else {
                    reject('token found but expired');                
                }

            } else {
                reject('token not found');            
            }
        });
    };


    lib.auth = (action, data) =>  {
        var req = new Request(action, {
            method: 'POST',
            headers: new Headers({
                'Content-type': 'application/json'            
            }),
            body: JSON.stringify(data)
        });

        return fetch(req).then(
            resp => {
                var res = resp.json();

                if (resp.ok) {
                    return res;
                } else {
                    throw res;                
                }
            }
        ).then(o => ({
                username: data.username,
                token: o.token
            }),
            o => o.then(o => Promise.reject(o.reason))
        );
    }

    const PROTO = 'minichat';

    var ChatStream = function (host, token) {
        this.host = host;
        this.token = token;
    };

    ChatStream.prototype.connect = function () {
        this.ws = new WebSocket(`ws://${this.host}/chat/${this.token}`, PROTO);

        this.ws.onerror = err => {
            if (this.onerror) {
                this.onerror(err);
            }
        };

        this.ws.onclose = err => {
            if (this.onclose) {
                this.onclose(err);
            }
        };

        this.ws.onmessage = (event) => {
            var parsed;

            console.log(event.data);

            try {
                parsed = JSON.parse(event.data);
            } catch (e) {
                console.error(e);
                return;
            }

            if (this.onmessage) {
                this.onmessage(parsed);
            }
        }
    }

    ChatStream.prototype.send = function (type, data, opts) {
        if (!this.ws) {
            throw new Error('not connected yet');
        }

        var msg = {
            type: type
        };

        if (data) {
            msg.content = data;
        }

        if (opts) {
            for (let key in opts) {
                msg[key] = opts[key];
            }
        }

        this.ws.send(JSON.stringify(msg));
    }

    lib.ChatStream = ChatStream;

    return lib;
})();


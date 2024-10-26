// 練習のためCookiesは使用せず自作する

class Cookie {
    // parser的な側面あり
    constructor(cookie = document.cookie) {
        this.cookie = cookie
    }

    getAllPare() {
        let cookies = {}

        const splitted_cookies = this.cookie.split('; ');
        splitted_cookies.forEach(function(cookie_pare) {
            const keyAndValue = cookie_pare.split('=');
            cookies[keyAndValue[0]] = keyAndValue[1]
        });
        return cookies
    }

    getAllKey() {
        let keys = []

        const splitted_cookies = this.cookie.split('; ');
        splitted_cookies.forEach(function(cookie_pare) {
            keys.push(cookie_pare.split('=')[0])
        });
        return keys
    }

    getAllValue() {
        let values = []

        const splitted_cookies = this.cookie.split('; ');
        splitted_cookies.forEach(function(cookie_pare) {
            values.push(cookie_pare.split('=')[1])
        });
        return values
    }

    getValue(key) {
        if(!this.cookie.includes('; ' + key + '=')) {return null}

        const splitted_cookies = this.cookie.split('; ');
        
        for(let i = 0; i < splitted_cookies.length; i++) {
            const keyAndValue = splitted_cookies[i].split('=');
            if(keyAndValue[0] == key) {
                return keyAndValue[1]
            }
        };
    }

    getKey(value) {
        if(!this.cookie.includes('=' + value + '; ')) {return null}

        const splitted_cookies = this.cookie.split('; ');
        
        for(let i = 0; i < splitted_cookies.length; i++) {
            const keyAndValue = splitted_cookies[i].split('=');
            if(keyAndValue[1] == value) {
                return keyAndValue[0]
            }
        };
    }

    hasKey(value) {
        return this.cookie.includes('=' + value + '; ') ? true : false
    }

    hasValue(key) {
        return this.cookie.includes('; ' + key + '=') ? true : false
    }

    getAllMatchKey(reg) {
        
        let keys = []

        const splitted_cookies = this.cookie.split('; ');
        splitted_cookies.forEach(function(cookie_pare) {
            const keyAndValue = cookie_pare.split('=')
            if(reg.test(keyAndValue[0])) {
                keys.push(splitted_cookie[0])
            }
        });
        
        return keys
    }

    set(key, value, options = []) {
        if(options.length) {
            let option_str = '';
            options.forEach(function(option) {
                option_str += option.join('=') + '; '
            })
            document.cookie = str(key + '=' + value + '; ' + option_str)
        } else {
            document.cookie = str(key + '=' + value)
        }
        return
    }
}
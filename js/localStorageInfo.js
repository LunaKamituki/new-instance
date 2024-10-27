/*
          localStorage
          
            settings(obj)
              | - history(obj)
                    | - enable(bool)
                    | - search(bool)
                    | - watch(bool)
              
            history(obj)
              | - search(arr)
              | - watch(arr)

            watchLater(arr)
*/

function setDefaultInfoToNoInfoLocalStorage(){

    try{
        const settings = localStorage.getItem('settings');
        const history= localStorage.getItem('history');
        const watchLater= localStorage.getItem('watchLater');

        if(!settings) {
            const default_settings = {
                history: {
                    enable: true,
                    search: true,
                    watch: true
                }
            }

            localStorage.setItem('settings', JSON.stringify(default_settings));
        }
        
        if(!history) {
            const default_history = {
                search: [],
                watch: []
            }
            const json_default_history = JSON.stringify(default_history);
            console.log(json_default_history)
            console.log(typeof json_default_history)
            localStorage.setItem('history', json_default_history);
        }

        if(!watchLater) {
            const default_watchLater = []
            localStorage.setItem('watchLater', JSON.stringify(default_watchLater));
        }
        
        return null
    } catch(e) {
        return e.message
    }
}
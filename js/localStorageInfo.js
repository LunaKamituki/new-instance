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
                search: {
                    history: []
                },
                watch: {
                    history: []
                }
            }

            localStorage.setItem('history', JSON.stringify(default_history));
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
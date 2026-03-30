import { writable } from 'svelte/store';

function createThemeStore() {
    const { subscribe, set: internalSet } = writable('midnight');
    
    const set = (value: string) => {
        if (typeof localStorage !== 'undefined') {
            localStorage.setItem('theme', value);
        }
        if (typeof document !== 'undefined') {
            document.documentElement.setAttribute('data-theme', value);
        }
        internalSet(value);
    };

    const init = () => {
        if (typeof localStorage !== 'undefined') {
            const saved = localStorage.getItem('theme');
            const valid = ['midnight', 'ember', 'synthwave'];
            if (saved && valid.includes(saved)) {
                set(saved);
            } else {
                set('midnight');
            }
        } else {
            set('midnight');
        }
    };

    return { subscribe, set, init };
}

export const theme = createThemeStore();

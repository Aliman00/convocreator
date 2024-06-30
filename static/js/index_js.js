/**
 * Template Editor Component
 * 
 * This component manages the conversation template editing functionality.
 * It handles template loading, saving, screen management, and Lua script generation.
 */
function templateEditor() {
    return {
        templateId: null,
        templateName: '',
        screens: [],
        selectedScreen: null,
        currentScreen: { options: [] },
        luaScript: '',
        templates: [],
        selectedTemplateId: '',

        /**
         * Initializes the component by fetching templates.
         */
        init() {
            this.fetchTemplates().catch(error => {
                console.error('Failed to fetch templates on init:', error);
            });
        },

        /**
         * Fetches all templates from the server.
         */
        async fetchTemplates() {
            try {
                const response = await fetch('/api/templates');
                if (!response.ok) {
                    throw new Error(`Failed to fetch templates: ${response.status} ${response.statusText}`);
                }
                this.templates = await response.json();
            } catch (error) {
                console.error('Error fetching templates:', error);
                alert(`Error fetching templates: ${error.message}`);
            }
        },

        /**
         * Loads a selected template from the server.
         */
        async loadTemplate() {
            if (!this.selectedTemplateId) {
                alert('Please select a template');
                return;
            }
        
            try {
                const response = await fetch(`/api/templates/${this.selectedTemplateId}`);
                if (!response.ok) {
                    throw new Error(`Failed to load template: ${response.status} ${response.statusText}`);
                }
                const template = await response.json();
                this.templateId = template.id;
                this.templateName = template.name;
                this.screens = template.screens;
                this.selectedScreen = null;
                this.currentScreen = { options: [] };
                
                await this.generateLua();
            } catch (error) {
                console.error('Error loading template:', error);
                alert(`Error loading template: ${error.message}`);
            }
        },

        /**
         * Adds a new screen for a specific option.
         * @param {number} optionIndex - The index of the option to add a screen for.
         */
        addScreenForOption(optionIndex) {
            const newScreen = this.addScreen();
            this.currentScreen.options[optionIndex].next_screen = newScreen.id;
            this.saveScreen();
            this.selectScreen(newScreen.id);
        },

        /**
         * Adds a new screen to the template.
         * @returns {Object} The newly created screen.
         */
        addScreen() {
            const newScreen = {
                id: Date.now(),
                id_name: `screen_${this.screens.length + 1}`,
                custom_dialog_text: '',
                stop_conversation: false,
                options: []
            };
            this.screens.push(newScreen);
            return newScreen;
        },

        /**
         * Gets the name of a screen by its ID.
         * @param {number} screenId - The ID of the screen.
         * @returns {string} The name of the screen or 'Unknown Screen' if not found.
         */
        getScreenName(screenId) {
            const screen = this.screens.find(s => s.id === screenId);
            return screen ? screen.id_name : 'Unknown Screen';
        },

        /**
         * Selects a screen for editing.
         * @param {number} id - The ID of the screen to select.
         */
        selectScreen(id) {
            this.selectedScreen = id;
            this.currentScreen = JSON.parse(JSON.stringify(this.screens.find(s => s.id === id)));
        },

        /**
         * Adds a new option to the current screen.
         */
        addOption() {
            this.currentScreen.options.push({ text: '', next_screen: null });
        },

        /**
         * Removes an option from the current screen.
         * @param {number} index - The index of the option to remove.
         */
        removeOption(index) {
            this.currentScreen.options.splice(index, 1);
        },

        /**
         * Saves changes to the current screen.
         */
        saveScreen() {
            const index = this.screens.findIndex(s => s.id === this.selectedScreen);
            if (index !== -1) {
                this.screens[index] = JSON.parse(JSON.stringify(this.currentScreen));
            }
        },

        /**
         * Removes a screen from the template.
         * @param {number} id - The ID of the screen to remove.
         */
        removeScreen(id) {
            if (this.screens.length > 1) {
                this.screens = this.screens.filter(screen => screen.id !== id);
                
                this.screens.forEach(screen => {
                    screen.options = screen.options.map(option => 
                        option.next_screen === id ? { ...option, next_screen: null } : option
                    );
                });

                if (this.selectedScreen === id) {
                    this.selectedScreen = null;
                    this.currentScreen = { options: [] };
                }

                if (this.screens[0].id === id) {
                    this.screens[0].id_name = 'first_screen';
                }
            }
        },

        /**
         * Saves the current template to the server.
         */
        async saveTemplate() {
            const template = {
                id: this.templateId,
                name: this.templateName,
                initial_screen: this.screens.length > 0 ? this.screens[0].id : null,
                screens: this.screens.map(screen => ({
                    id: screen.id,
                    id_name: screen.id_name,
                    custom_dialog_text: screen.custom_dialog_text,
                    stop_conversation: screen.stop_conversation,
                    options: screen.options.map(option => ({
                        id: option.id,
                        text: option.text,
                        next_screen: option.next_screen
                    }))
                }))
            };
        
            console.log('Sending template data:', JSON.stringify(template, null, 2));
        
            const url = this.templateId ? `/api/templates/${this.templateId}` : '/api/templates';
            const method = this.templateId ? 'PUT' : 'POST';
        
            try {
                const response = await fetch(url, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(template),
                });
        
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(JSON.stringify(errorData));
                }
        
                const responseData = await response.json();
                console.log('Response:', response.status, responseData);
        
                if (!this.templateId) {
                    this.templateId = responseData.id;
                }
                alert('Template saved successfully');
                await this.fetchTemplates();
            } catch (error) {
                console.error('Error saving template:', error);
                alert(`Error saving template: ${error.message}`);
            }
        },

        /**
         * Generates a Lua script for the current template.
         */
        async generateLua() {
            if (!this.templateId) {
                alert('Please load or save a template first');
                return;
            }

            try {
                const response = await fetch(`/api/templates/${this.templateId}/lua`);
                if (!response.ok) {
                    throw new Error('Failed to generate Lua script');
                }
                const result = await response.json();
                this.luaScript = result.lua_script;
            } catch (error) {
                console.error('Error generating Lua script:', error);
                alert(`Error generating Lua script: ${error.message}`);
            }
        }
    };
}
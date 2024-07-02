/**
 * Template Editor Component
 * 
 * This component manages the conversation template editing functionality.
 * It handles template loading, saving, screen management, and Lua script generation.
 */
function templateEditor() {
    return {
        // State variables
        templateId: null,
        templateName: '',
        screens: [],
        selectedScreen: null,
        currentScreen: { options: [] },
        luaScript: '',
        templates: [],
        selectedTemplateId: '',
        stfMode: false,
        stfData: {},
        stfFile: null,

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
                this.stfMode = template.stf_mode;
                
                // Handle stfData
                if (template.stf_mode) {
                    this.stfData = {};
                    this.screens.forEach(screen => {
                        if (screen.leftDialog) {
                            const leftDialogId = screen.leftDialog.split(':')[1];
                            this.stfData[leftDialogId] = screen.custom_dialog_text;
                        }
                        screen.options.forEach(option => {
                            if (option.stfReference) {
                                const optionTextId = option.stfReference.split(':')[1];
                                this.stfData[optionTextId] = option.text;
                            }
                        });
                    });
                } else {
                    this.stfData = {};
                }
                
                await this.generateLua();
            } catch (error) {
                console.error('Error loading template:', error);
                alert(`Error loading template: ${error.message}`);
            }
        },

        /**
         * Deletes the selected template from the server.
         */
        async deleteTemplate() {
            if (!this.selectedTemplateId) {
                alert('Please select a template to delete');
                return;
            }
        
            if (!confirm('Are you sure you want to delete this template?')) {
                return;
            }
        
            try {
                const response = await fetch(`/api/templates/${this.selectedTemplateId}`, {
                    method: 'DELETE',
                });
        
                if (!response.ok) {
                    throw new Error('Failed to delete template');
                }
        
                alert('Template deleted successfully');
                this.resetEditorState();
                await this.fetchTemplates();
            } catch (error) {
                console.error('Error deleting template:', error);
                alert(`Error deleting template: ${error.message}`);
            }
        },

        /**
         * Resets the editor state.
         */
        resetEditorState() {
            this.selectedTemplateId = '';
            this.templateId = null;
            this.templateName = '';
            this.screens = [];
            this.selectedScreen = null;
            this.currentScreen = { options: [] };
            this.luaScript = '';
            this.stfMode = false;
            this.stfData = {};
            this.stfFile = null;
        },

        /**
         * Toggles between STF mode and regular mode
         */
        toggleSTFMode() {
            this.stfMode = !this.stfMode;
            if (this.stfMode) {
                this.convertToSTFMode();
            } else {
                this.convertFromSTFMode();
            }
            
            // Update currentScreen if one is selected
            if (this.selectedScreen !== null) {
                this.currentScreen = JSON.parse(JSON.stringify(this.screens.find(s => s.id === this.selectedScreen)));
            }
        },

        /**
         * Converts the current template to STF mode
         */
        convertToSTFMode() {
            this.screens = this.screens.map(screen => {
                const leftDialogId = screen.leftDialog ? screen.leftDialog.split(':')[1] : `s_${this.generateUniqueId()}`;
                this.stfData[leftDialogId] = screen.custom_dialog_text;
                return {
                    ...screen,
                    leftDialog: `@conversation/${this.templateName}:${leftDialogId}`,
                    options: screen.options.map(option => {
                        const optionTextId = option.stfReference ? option.stfReference.split(':')[1] : `s_${this.generateUniqueId()}`;
                        this.stfData[optionTextId] = option.text;
                        return {
                            ...option,
                            stfReference: `@conversation/${this.templateName}:${optionTextId}`
                        };
                    })
                };
            });
        },
        
        /**
         * Converts the current template from STF mode to regular mode
         */
        convertFromSTFMode() {
            this.screens = this.screens.map(screen => ({
                ...screen,
                custom_dialog_text: screen.leftDialog ? (this.stfData[screen.leftDialog.split(':')[1]] || screen.custom_dialog_text) : screen.custom_dialog_text,
                options: screen.options.map(option => ({
                    ...option,
                    text: option.stfReference ? (this.stfData[option.stfReference.split(':')[1]] || option.text) : option.text
                }))
            }));
            this.stfData = {};
        },

        /**
         * Generates a unique ID for STF references
         */
        generateUniqueId() {
            return Math.random().toString(36).substr(2, 8);
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
                leftDialog: '',
                stop_conversation: false,
                options: []
            };
            if (this.stfMode) {
                const leftDialogId = `s_${this.generateUniqueId()}`;
                this.stfData[leftDialogId] = '';
                newScreen.leftDialog = `@conversation/${this.templateName}:${leftDialogId}`;
            }
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
            const newOption = { text: '', next_screen: null };
            if (this.stfMode) {
                const optionTextId = `s_${this.generateUniqueId()}`;
                this.stfData[optionTextId] = '';
                newOption.stfReference = `@conversation/${this.templateName}:${optionTextId}`;
            }
            this.currentScreen.options.push(newOption);
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
                if (this.stfMode) {
                    const leftDialogId = this.currentScreen.leftDialog.split(':')[1];
                    this.stfData[leftDialogId] = this.currentScreen.custom_dialog_text;
                    this.currentScreen.options.forEach(option => {
                        const optionTextId = option.stfReference.split(':')[1];
                        this.stfData[optionTextId] = option.text;
                    });
                }
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
                stf_mode: this.stfMode,
                initial_screen: this.screens.length > 0 ? this.screens[0].id : null,
                screens: this.screens.map(screen => ({
                    id: screen.id,
                    id_name: screen.id_name,
                    custom_dialog_text: screen.custom_dialog_text,
                    leftDialog: screen.leftDialog,
                    stop_conversation: screen.stop_conversation,
                    options: screen.options.map(option => ({
                        id: option.id,
                        text: option.text,
                        stfReference: option.stfReference,
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
        },

        /**
         * Downloads the generated Lua script.
         */
        downloadLua() {
            if (!this.luaScript) {
                alert('Please generate the Lua script first.');
                return;
            }

            const element = document.createElement('a');
            const file = new Blob([this.luaScript], {type: 'text/plain'});
            element.href = URL.createObjectURL(file);
            element.download = `${this.templateName || 'script'}.lua`;
            document.body.appendChild(element);
            element.click();
            document.body.removeChild(element);
        },

        /**
         * Downloads the STF file.
         */
        async downloadSTF() {
            if (!this.stfMode) {
                alert('STF mode is not enabled.');
                return;
            }

            const stfData = this.generateSTFData();
            
            try {
                const response = await fetch('/api/templates/stf', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        templateName: this.templateName,
                        data: stfData
                    }),
                });

                if (!response.ok) {
                    throw new Error('Failed to generate STF file');
                }

                // Get the blob from the response
                const blob = await response.blob();

                // Create a link and trigger the download
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = `${this.templateName || 'conversation'}.stf`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
            } catch (error) {
                console.error('Error downloading STF file:', error);
                alert(`Error downloading STF file: ${error.message}`);
            }
        },

        /**
         * Generates STF data from the current template
         * @returns {Array} An array of STF data entries
         */
        generateSTFData() {
            let data = [];
            this.screens.forEach(screen => {
                const leftDialogId = screen.leftDialog.split(':')[1];
                data.push([leftDialogId, screen.custom_dialog_text]);
                screen.options.forEach(option => {
                    const optionTextId = option.stfReference.split(':')[1];
                    data.push([optionTextId, option.text]);
                });
            });
            return data;
        }
    };
}
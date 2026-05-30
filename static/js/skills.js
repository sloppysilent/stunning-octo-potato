// skills.js - логика управления навыками
document.addEventListener('DOMContentLoaded', function() {
    const addSkillBtn = document.getElementById('add-skill-btn');
    const skillInputWrapper = document.getElementById('skill-input-wrapper');
    const skillInput = document.getElementById('skill-input');
    const skillSuggestions = document.getElementById('skill-suggestions');
    const skillsContainer = document.getElementById('skills-container');
    
    if (!addSkillBtn) return; 

    addSkillBtn.addEventListener('click', function() {
        addSkillBtn.style.display = 'none';
        skillInputWrapper.style.display = 'block';
        skillInput.focus();
    });

    let debounceTimer;
    skillInput.addEventListener('input', function() {
        clearTimeout(debounceTimer);
        const query = this.value.trim();
        
        if (query.length < 1) {
            skillSuggestions.innerHTML = '';
            return;
        }
        
        debounceTimer = setTimeout(() => {
            fetch(`/users/skills/?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    renderSuggestions(data);
                })
                .catch(error => console.error('Error:', error));
        }, 300);
    });

    skillInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            const skillName = this.value.trim();
            if (skillName) {
                addSkill(null, skillName);
            }
        }
    });
    
    function renderSuggestions(skills) {
        skillSuggestions.innerHTML = '';
        
        skills.forEach(skill => {
            const li = document.createElement('li');
            li.textContent = skill.name;
            li.className = 'skill-suggestion';
            li.addEventListener('click', () => {
                addSkill(skill.id, null);
            });
            skillSuggestions.appendChild(li);
        });

        const currentValue = skillInput.value.trim();
        const exists = skills.some(s => s.name.toLowerCase() === currentValue.toLowerCase());
        
        if (!exists && currentValue) {
            const li = document.createElement('li');
            li.textContent = `Создать "${currentValue}"`;
            li.className = 'skill-suggestion create-new';
            li.addEventListener('click', () => {
                addSkill(null, currentValue);
            });
            skillSuggestions.appendChild(li);
        }
    }
    
    function addSkill(skillId, skillName) {
        const userId = skillInput.dataset.userId;
        const formData = new FormData();
        formData.append('csrfmiddlewaretoken', getCSRFToken());
        
        if (skillId) {
            formData.append('skill_id', skillId);
        } else if (skillName) {
            formData.append('name', skillName);
        }
        
        fetch(`/users/${userId}/skills/add/`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.added) {
                const tag = createSkillTag(data.skill_id, data.name);
                skillsContainer.appendChild(tag);

                skillInput.value = '';
                skillSuggestions.innerHTML = '';
                skillInputWrapper.style.display = 'none';
                addSkillBtn.style.display = 'inline-block';
            }
        })
        .catch(error => console.error('Error:', error));
    }
    
    function createSkillTag(skillId, skillName) {
        const userId = skillInput.dataset.userId;
        const span = document.createElement('span');
        span.className = 'skill-tag';
        span.innerHTML = `
            ${skillName}
            <button type="button" class="skill-remove" 
                    data-skill-id="${skillId}" 
                    data-user-id="${userId}">×</button>
        `;

        const removeBtn = span.querySelector('.skill-remove');
        removeBtn.addEventListener('click', function() {
            removeSkill(this.dataset.skillId, this.dataset.userId, span);
        });
        
        return span;
    }
    
    function removeSkill(skillId, userId, element) {
        const formData = new FormData();
        formData.append('csrfmiddlewaretoken', getCSRFToken());
        
        fetch(`/users/${userId}/skills/${skillId}/remove/`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'ok') {
                element.remove();
            }
        })
        .catch(error => console.error('Error:', error));
    }
    
    function getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
               document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1];
    }

    document.querySelectorAll('.skill-remove').forEach(btn => {
        btn.addEventListener('click', function() {
            const skillId = this.dataset.skillId;
            const userId = this.dataset.userId;
            const tag = this.closest('.skill-tag');
            removeSkill(skillId, userId, tag);
        });
    });
});
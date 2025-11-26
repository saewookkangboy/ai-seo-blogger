/**
 * 폼 검증 컴포넌트
 */

export class FormValidator {
    constructor(formElement) {
        this.form = formElement;
        this.errors = {};
        this.setupValidation();
    }

    /**
     * 검증 규칙 설정
     */
    setupValidation() {
        // URL 검증
        const urlInput = document.getElementById('url_input');
        if (urlInput) {
            urlInput.addEventListener('blur', () => this.validateURL(urlInput));
            urlInput.addEventListener('input', () => this.clearError(urlInput));
        }

        // 텍스트 입력 검증
        const textInput = document.getElementById('text_input');
        if (textInput) {
            textInput.addEventListener('blur', () => this.validateText(textInput));
            textInput.addEventListener('input', () => this.clearError(textInput));
        }

        // 실시간 검증
        this.form?.addEventListener('submit', (e) => {
            if (!this.validateAll()) {
                e.preventDefault();
                e.stopPropagation();
            }
        });
    }

    /**
     * URL 검증
     */
    validateURL(input) {
        const value = input.value.trim();
        
        if (value && !this.isValidURL(value)) {
            this.showError(input, '올바른 URL 형식이 아닙니다.');
            return false;
        }
        
        this.clearError(input);
        return true;
    }

    /**
     * 텍스트 입력 검증
     */
    validateText(input) {
        const value = input.value.trim();
        const urlInput = document.getElementById('url_input');
        const urlValue = urlInput?.value.trim() || '';

        if (!value && !urlValue) {
            this.showError(input, '주제/문맥 또는 URL을 입력해주세요.');
            return false;
        }

        if (value && value.length < 10) {
            this.showError(input, '최소 10자 이상 입력해주세요.');
            return false;
        }

        this.clearError(input);
        return true;
    }

    /**
     * 전체 검증
     */
    validateAll() {
        const urlInput = document.getElementById('url_input');
        const textInput = document.getElementById('text_input');

        let isValid = true;

        if (urlInput && urlInput.value.trim()) {
            isValid = this.validateURL(urlInput) && isValid;
        }

        if (textInput) {
            isValid = this.validateText(textInput) && isValid;
        }

        // 최소 하나는 입력되어야 함
        const urlValue = urlInput?.value.trim() || '';
        const textValue = textInput?.value.trim() || '';

        if (!urlValue && !textValue) {
            if (textInput) {
                this.showError(textInput, '주제/문맥 또는 URL을 입력해주세요.');
            }
            isValid = false;
        }

        return isValid;
    }

    /**
     * URL 형식 검증
     */
    isValidURL(string) {
        try {
            const url = new URL(string);
            return url.protocol === 'http:' || url.protocol === 'https:';
        } catch (_) {
            return false;
        }
    }

    /**
     * 에러 표시
     */
    showError(input, message) {
        this.clearError(input);

        input.classList.add('error');
        input.setAttribute('aria-invalid', 'true');

        const errorDiv = document.createElement('div');
        errorDiv.className = 'form-feedback error';
        errorDiv.textContent = message;
        errorDiv.id = `${input.id}-error`;

        input.setAttribute('aria-describedby', errorDiv.id);
        input.parentElement.appendChild(errorDiv);
    }

    /**
     * 에러 제거
     */
    clearError(input) {
        input.classList.remove('error');
        input.removeAttribute('aria-invalid');
        input.removeAttribute('aria-describedby');

        const errorId = `${input.id}-error`;
        const errorDiv = document.getElementById(errorId);
        if (errorDiv) {
            errorDiv.remove();
        }
    }

    /**
     * 성공 표시
     */
    showSuccess(input, message) {
        this.clearError(input);

        const successDiv = document.createElement('div');
        successDiv.className = 'form-feedback success';
        successDiv.textContent = message;
        successDiv.id = `${input.id}-success`;

        input.parentElement.appendChild(successDiv);

        setTimeout(() => {
            successDiv.remove();
        }, 3000);
    }
}


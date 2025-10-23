/**
 * PostCrafterPro - Alpine.js Component
 * Tinder形式のSNS投稿作成アプリケーション
 */

function postCreator() {
    return {
        // ========================================
        // State Management
        // ========================================

        // Current step (1-8)
        currentStep: 1,

        // Computed properties for template compatibility
        get step() {
            return this.currentStep;
        },
        set step(value) {
            this.currentStep = value;
        },
        get progress() {
            return this.getProgressPercentage();
        },

        // Loading state
        loading: false,

        // Form data
        form: {
            date: new Date().toISOString().split('T')[0], // Default to today
            url: '',
            decided: '',
            anniversary: '',
            remarks: ''
        },

        // Context results
        pineconeResults: [],
        similarPosts: [],
        analyticsInsights: '', // X Analytics performance insights

        // Current round posts
        postA: null,
        postB: null,

        // Selection state
        selectedSide: null, // 'A' or 'B'

        // Round tracking
        round: 1,
        history: [], // Array of {round, postA, postB, selected, refinementRequest}

        // Refinement input
        refinementRequest: '',

        // Final selected post
        finalPost: null,

        // Error message
        errorMessage: '',

        // Publishing state
        publishing: false,

        // Computed properties for final post
        get finalPostLength() {
            return this.finalPost ? this.finalPost.character_count || this.finalPost.text?.length || 0 : 0;
        },
        get finalPostValid() {
            return this.finalPost ? this.finalPost.is_valid : false;
        },

        // ========================================
        // Initialization
        // ========================================

        init() {
            console.log('PostCrafterPro initialized');
            this.setTodayDate();
        },

        setTodayDate() {
            this.form.date = new Date().toISOString().split('T')[0];
        },

        // ========================================
        // Step 1: Fetch Context (Pinecone + Similar Posts)
        // ========================================

        async fetchContext() {
            if (!this.validateForm()) {
                return;
            }

            this.loading = true;
            this.errorMessage = '';

            // Move to step 2 (loading screen) first
            this.currentStep = 2;

            // Small delay to show loading animation
            await new Promise(resolve => setTimeout(resolve, 100));

            try {
                const response = await fetch('/api/init', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        date: this.form.date,
                        url: this.form.url,
                        decided: this.form.decided,
                        anniversary: this.form.anniversary,
                        remarks: this.form.remarks
                    })
                });

                if (!response.ok) {
                    throw new Error('コンテキストの取得に失敗しました');
                }

                const data = await response.json();

                this.pineconeResults = data.pinecone_results || [];
                this.similarPosts = data.similar_posts || [];
                this.analyticsInsights = data.analytics_insights || '';

                // Pinecone結果がない場合は直接生成に進む
                if (!this.pineconeResults || this.pineconeResults.length === 0) {
                    console.log('Pinecone結果なし - 直接投稿生成に進みます');
                    // Step 3をスキップして直接生成処理へ
                    await this.proceedToGeneration();
                } else {
                    // Pinecone結果がある場合はStep 3を表示
                    this.currentStep = 3;
                }

            } catch (error) {
                console.error('Error fetching context:', error);
                this.errorMessage = error.message || 'コンテキストの取得中にエラーが発生しました';
                // Go back to step 1 on error
                this.currentStep = 1;
            } finally {
                this.loading = false;
            }
        },

        validateForm() {
            if (!this.form.date) {
                this.errorMessage = '投稿日を入力してください';
                return false;
            }
            if (!this.form.url) {
                this.errorMessage = '商品URLを入力してください';
                return false;
            }
            if (!this.form.decided) {
                this.errorMessage = '決定事項を入力してください';
                return false;
            }
            return true;
        },

        // ========================================
        // Step 3 → Step 4: Generate Initial Posts
        // ========================================

        async proceedToGeneration() {
            this.loading = true;
            this.errorMessage = '';

            // Move to step 4 (loading screen) first
            this.currentStep = 4;

            // Small delay to show loading animation
            await new Promise(resolve => setTimeout(resolve, 100));

            try {
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        date: this.form.date,
                        url: this.form.url,
                        decided: this.form.decided,
                        anniversary: this.form.anniversary,
                        remarks: this.form.remarks,
                        pinecone_results: this.pineconeResults,
                        similar_posts: this.similarPosts,
                        analytics_insights: this.analyticsInsights
                    })
                });

                if (!response.ok) {
                    throw new Error('投稿の生成に失敗しました');
                }

                const data = await response.json();

                this.postA = data.post_a;
                this.postB = data.post_b;
                this.round = 1;
                this.selectedSide = null;

                // Move to step 5 (Tinder view)
                this.currentStep = 5;

            } catch (error) {
                console.error('Error generating posts:', error);
                this.errorMessage = error.message || '投稿の生成中にエラーが発生しました';
                // Go back to step 3 on error
                this.currentStep = 3;
            } finally {
                this.loading = false;
            }
        },

        // ========================================
        // Step 5: Tinder Selection
        // ========================================

        selectPost(side) {
            this.selectedSide = side;
            console.log(`Selected: ${side}`);
        },

        getSelectedPost() {
            if (this.selectedSide === 'A') {
                return this.postA;
            } else if (this.selectedSide === 'B') {
                return this.postB;
            }
            return null;
        },

        getSelectedPostText() {
            const post = this.getSelectedPost();
            return post ? post.text : '投稿を選択してください';
        },

        // Move to refinement step
        proceedToRefinement() {
            if (!this.selectedSide) {
                this.errorMessage = '投稿を選択してください';
                return;
            }

            // Save current round to history
            this.saveRoundToHistory();

            // Move to step 6 (refinement)
            this.currentStep = 6;
            this.refinementRequest = '';
        },

        // Skip refinement and finalize
        finalizeSelection() {
            if (!this.selectedSide) {
                this.errorMessage = '投稿を選択してください';
                return;
            }

            // Save current round to history
            this.saveRoundToHistory();

            // Set final post
            this.finalPost = this.getSelectedPost();

            // Move to step 7 (confirmation)
            this.currentStep = 7;
        },

        saveRoundToHistory() {
            this.history.push({
                round: this.round,
                postA: { ...this.postA },
                postB: { ...this.postB },
                selected: this.selectedSide,
                refinementRequest: this.refinementRequest || ''
            });
        },

        // ========================================
        // Step 6: Refinement
        // ========================================

        async refinePost() {
            if (!this.selectedSide) {
                this.errorMessage = '投稿を選択してください';
                return;
            }

            this.loading = true;
            this.errorMessage = '';

            try {
                const selectedPost = this.getSelectedPost();

                const response = await fetch('/api/refine', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        selected_post: selectedPost.text,
                        refinement_request: this.refinementRequest,
                        round: this.round
                    })
                });

                if (!response.ok) {
                    throw new Error('投稿の改善に失敗しました');
                }

                const data = await response.json();

                // Update posts with refined versions
                this.postA = data.post_a;
                this.postB = data.post_b;
                this.round += 1;
                this.selectedSide = null;

                // Go back to Tinder view (step 5)
                this.currentStep = 5;

            } catch (error) {
                console.error('Error refining post:', error);
                this.errorMessage = error.message || '投稿の改善中にエラーが発生しました';
            } finally {
                this.loading = false;
            }
        },

        skipRefinement() {
            // Set final post
            this.finalPost = this.getSelectedPost();

            // Move to step 7 (confirmation)
            this.currentStep = 7;
        },

        // ========================================
        // Step 7: Confirmation & Publishing
        // ========================================

            async confirmAndPublish() {
            this.loading = true;
            this.publishing = true;
            this.errorMessage = '';

            try {
                const response = await fetch('/api/publish', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        date: this.form.date,
                        url: this.form.url,
                        decided: this.form.decided,
                        anniversary: this.form.anniversary,
                        remarks: this.form.remarks,
                        final_post: this.finalPost,
                        history: this.history,
                        pinecone_results: this.pineconeResults,
                        similar_posts: this.similarPosts
                    })
                });

                if (!response.ok) {
                    throw new Error('投稿の保存に失敗しました');
                }

                const data = await response.json();
                console.log('Published:', data);

                // Move to step 8 (success)
                this.currentStep = 8;

            } catch (error) {
                console.error('Error publishing post:', error);
                this.errorMessage = error.message || '投稿の保存中にエラーが発生しました';
            } finally {
                this.loading = false;
                this.publishing = false;
            }
        },

        editPost() {
            // Go back to Tinder view
            this.currentStep = 5;
        },

        // ========================================
        // Step 8: Success & Start Over
        // ========================================

        startOver() {
            // Reset all state
            this.currentStep = 1;
            this.loading = false;
            this.publishing = false;
            this.form = {
                date: new Date().toISOString().split('T')[0],
                url: '',
                decided: '',
                anniversary: '',
                remarks: ''
            };
            this.pineconeResults = [];
            this.similarPosts = [];
            this.analyticsInsights = '';
            this.postA = null;
            this.postB = null;
            this.selectedSide = null;
            this.round = 1;
            this.history = [];
            this.refinementRequest = '';
            this.finalPost = null;
            this.errorMessage = '';
        },

        // ========================================
        // Utility Methods
        // ========================================

        getProgressPercentage() {
            return (this.currentStep / 8) * 100;
        },

        getProgressText() {
            return `ステップ ${this.currentStep}/8: ${this.getStepLabel(this.currentStep)}`;
        },

        getStepLabel(step) {
            const labels = {
                1: '情報入力',
                2: 'コンテキスト読込中',
                3: 'コンテキスト確認',
                4: '投稿生成中',
                5: '投稿選択',
                6: '改善リクエスト',
                7: '最終確認',
                8: '完了'
            };
            return labels[step] || '';
        },

        // Alias for template compatibility
        generateInitialPosts() {
            return this.proceedToGeneration();
        },

        publishPost() {
            this.publishing = true;
            return this.confirmAndPublish();
        },

        restart() {
            return this.startOver();
        },

        goBack() {
            // ステップごとの戻る処理
            if (this.currentStep === 3) {
                // Step 3 → Step 1: 入力フォームに戻る
                this.currentStep = 1;
            } else if (this.currentStep === 5) {
                // Step 5 → Step 3: コンテキスト結果に戻る
                this.currentStep = 3;
            } else if (this.currentStep === 6) {
                // Step 6 → Step 5: 投稿選択に戻る
                this.currentStep = 5;
                this.refinementRequest = ''; // リクエストをクリア
            } else if (this.currentStep === 7) {
                // Step 7 → Step 5: 投稿選択に戻って再選択
                this.currentStep = 5;
            } else {
                // その他の場合は1つ前のステップに戻る
                if (this.currentStep > 1) {
                    this.currentStep -= 1;
                }
            }
        },

        formatDate(dateString) {
            if (!dateString) return '';
            const date = new Date(dateString);
            return date.toLocaleDateString('ja-JP');
        },

        // Copy text to clipboard
        async copyToClipboard(text) {
            try {
                await navigator.clipboard.writeText(text);
                this.showCopyNotification();
            } catch (err) {
                console.error('Failed to copy:', err);
                // Fallback for older browsers
                this.copyToClipboardFallback(text);
            }
        },

        // Fallback copy method for older browsers
        copyToClipboardFallback(text) {
            const textarea = document.createElement('textarea');
            textarea.value = text;
            textarea.style.position = 'fixed';
            textarea.style.opacity = '0';
            document.body.appendChild(textarea);
            textarea.select();
            try {
                document.execCommand('copy');
                this.showCopyNotification();
            } catch (err) {
                console.error('Fallback copy failed:', err);
                alert('コピーに失敗しました');
            }
            document.body.removeChild(textarea);
        },

        // Show copy success notification
        showCopyNotification() {
            // Create notification element
            const notification = document.createElement('div');
            notification.className = 'fixed bottom-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg flex items-center space-x-2 z-50 animate-fade-in';
            notification.innerHTML = `
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                </svg>
                <span>コピーしました！</span>
            `;
            document.body.appendChild(notification);

            // Remove after 2 seconds
            setTimeout(() => {
                notification.style.opacity = '0';
                notification.style.transition = 'opacity 0.3s';
                setTimeout(() => {
                    document.body.removeChild(notification);
                }, 300);
            }, 2000);
        }
    };
}

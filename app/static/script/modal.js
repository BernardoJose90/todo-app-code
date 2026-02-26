$(document).ready(function() {
    console.log('🔧 modal.js loaded - ADVANCED VERSION');

    // Initialize modal
    let taskModal = null;
    if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
        taskModal = new bootstrap.Modal(document.getElementById('task-modal'));
    }

    // Debug: Check button visibility
    console.log('🔍 Total edit buttons found:', $('.edit').length);
    console.log('🔍 Total delete buttons found:', $('.delete').length);

    // Initialize advanced features
    initViewToggle();
    initSearch();
    initKanbanDragAndDrop();
    highlightDueDates();

    // DRAG-AND-DROP for table view
    new Sortable(document.getElementById('task-table-body'), {
        animation: 150,
        handle: '.task-content',
        onEnd: function(evt) {
            let order = [];
            $('#task-table-body tr').each(function(index) {
                order.push({ id: $(this).data('id'), position: index });
            });

            $.ajax({
                url: '/tasks/reorder',
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ tasks: order }),
                success: function(response) {
                    console.log('✅ Task order updated');
                },
                error: function(xhr, status, error) {
                    console.error('❌ Error updating order:', error);
                    alert("Error updating task order: " + error);
                }
            });
        }
    });

    // FILTER TASKS
    $('.filter-btn').on('click', function() {
        const status = $(this).data('status');
        $('.filter-btn').removeClass('active');
        $(this).addClass('active');
        
        // Filter all views
        filterTasksByStatus(status);
        updateStats();
    });

    // SUBMIT HANDLER
    function setupSubmit(taskId = null) {
        $('#submit-task').off('click').on('click', function() {
            const description = $('#task-desc').val();
            const status = $('#task-status').val();
            const priority = $('#task-priority').val();
            const due_date = $('#task-due-date').val();

            console.log('💾 Saving task:', { taskId, description, status, priority, due_date });

            if (!description) {
                alert("Please enter a task!");
                return;
            }

            let url = '/tasks';
            let method = 'POST';
            
            if (taskId) {
                url = `/tasks/${taskId}`;
                method = 'PUT';
            }

            $.ajax({
                url: url,
                type: method,
                contentType: 'application/json',
                data: JSON.stringify({ 
                    description: description,
                    status: status, 
                    priority: priority, 
                    due_date: due_date 
                }),
                success: function(response) {
                    console.log('✅ Task saved successfully');
                    hideModal();
                    resetModal();
                    refreshTable();
                },
                error: function(xhr, status, error) {
                    console.error('❌ Error saving task:', error);
                    alert("Error saving task: " + error);
                }
            });
        });
    }

    // RESET MODAL
    function resetModal() {
        $('#task-desc').val('');
        $('#task-status').val('Todo');
        $('#task-priority').val('Medium');
        $('#task-due-date').val('');
        $('#modal-title').text('Add New Task');
        $('#submit-task').off('click');
    }

    // MODAL FUNCTIONS
    function showModal() {
        if (taskModal) {
            taskModal.show();
        } else {
            $('#task-modal').modal('show');
        }
    }

    function hideModal() {
        if (taskModal) {
            taskModal.hide();
        } else {
            $('#task-modal').modal('hide');
        }
    }

    // NEW TASK
    $(document).on('click', '#add-task-btn, #add-task-btn-empty', function(e) {
        console.log('➕ New Task button clicked');
        resetModal();
        setupSubmit();
        showModal();
    });

    // EDIT TASK - ENHANCED VERSION
    $(document).on('click', '.edit', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const taskId = $(this).data('id');
        const card = $(this).closest('.task-card, tr');
        
        console.log('🎯 EDIT BUTTON CLICKED - ID:', taskId);

        // Extract data from card or table row
        let description, status, priority, dueDate;
        
        if (card.hasClass('task-card')) {
            // Card view
            description = card.find('.task-title').text().trim();
            status = card.data('status');
            priority = card.find('.task-priority').text().trim();
            dueDate = card.find('.due-date').text().trim();
        } else {
            // Table view
            description = card.find('td').eq(1).find('.fw-semibold').text().trim();
            status = card.data('status');
            priority = card.find('td').eq(3).find('.badge').text().trim();
            dueDate = card.find('td').eq(4).text().trim();
            if (dueDate === '-') dueDate = '';
        }

        console.log('📝 EXTRACTED DATA:', { description, status, priority, dueDate });

        // Populate modal fields
        $('#task-desc').val(description);
        $('#task-status').val(status);
        $('#task-priority').val(priority);
        $('#task-due-date').val(dueDate);
        $('#modal-title').text('Edit Task');

        // Setup submit handler for this specific task
        setupSubmit(taskId);
        
        // Show modal
        showModal();
    });

    // DELETE TASK
    $(document).on('click', '.delete', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const taskId = $(this).data('id');
        console.log('🗑️ Deleting task ID:', taskId);

        if (!confirm("Are you sure you want to delete this task?")) return;

        $.ajax({
            url: `/tasks/${taskId}`,
            type: 'DELETE',
            success: function(response) {
                console.log('✅ Delete successful');
                refreshTable();
            },
            error: function(xhr, status, error) {
                console.error('❌ Error deleting task:', error);
                alert("Error deleting task: " + error);
            }
        });
    });

    // VIEW TOGGLE FUNCTIONALITY
    function initViewToggle() {
        $('.view-btn').on('click', function() {
            const view = $(this).data('view');
            $('.view-btn').removeClass('active');
            $(this).addClass('active');
            
            // Hide all views
            $('.view-section').hide();
            
            // Show selected view
            $(`#${view}-view`).show();
            
            // Reinitialize features for the active view
            if (view === 'kanban') {
                initKanbanDragAndDrop();
            }
            
            updateStats();
        });
    }

    // SEARCH FUNCTIONALITY
    function initSearch() {
        $('#task-search').on('input', function() {
            const searchTerm = $(this).val().toLowerCase();
            filterTasksBySearch(searchTerm);
            updateStats();
        });
    }

    // FILTER TASKS BY SEARCH
    function filterTasksBySearch(searchTerm) {
        $('.task-card, #task-table-body tr').each(function() {
            const text = $(this).text().toLowerCase();
            if (text.includes(searchTerm)) {
                $(this).show();
            } else {
                $(this).hide();
            }
        });
    }

    // FILTER TASKS BY STATUS
    function filterTasksByStatus(status) {
        $('.task-card, #task-table-body tr').each(function() {
            if (status === 'All' || $(this).data('status') === status) {
                $(this).show();
            } else {
                $(this).hide();
            }
        });
    }

    // KANBAN DRAG AND DROP
    function initKanbanDragAndDrop() {
        $('.kanban-cards').each(function() {
            new Sortable(this, {
                group: 'kanban',
                animation: 150,
                onEnd: function(evt) {
                    const taskId = evt.item.dataset.id;
                    const newStatus = evt.to.closest('.kanban-column').dataset.status;
                    
                    console.log(`🔄 Moving task ${taskId} to ${newStatus}`);
                    
                    $.ajax({
                        url: `/tasks/${taskId}`,
                        type: 'PUT',
                        contentType: 'application/json',
                        data: JSON.stringify({ status: newStatus }),
                        success: function(response) {
                            console.log('✅ Task status updated');
                            updateStats();
                        },
                        error: function(xhr, status, error) {
                            console.error('❌ Error updating task status:', error);
                        }
                    });
                }
            });
        });
    }

    // DUE DATE HIGHLIGHTING
    function highlightDueDates() {
        const today = new Date();
        
        $('.task-card').each(function() {
            const dueDateText = $(this).find('.due-date').text();
            if (dueDateText) {
                const dueDate = new Date(dueDateText);
                const diffTime = dueDate - today;
                const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
                
                $(this).removeClass('overdue due-soon');
                
                if (diffDays < 0) {
                    $(this).addClass('overdue');
                } else if (diffDays <= 3) {
                    $(this).addClass('due-soon');
                }
            }
        });
    }

    // REFRESH TABLE
    function refreshTable() {
        console.log('🔄 Refreshing table...');
        location.reload();
    }

    // UPDATE STATS
    function updateStats() {
        const total = $('.task-card:visible, #task-table-body tr:visible').length;
        const todo = $('.task-card[data-status="Todo"]:visible, #task-table-body tr[data-status="Todo"]:visible').length;
        const progress = $('.task-card[data-status="In Progress"]:visible, #task-table-body tr[data-status="In Progress"]:visible').length;
        const done = $('.task-card[data-status="Done"]:visible, #task-table-body tr[data-status="Done"]:visible').length;
        
        $('#total-tasks').text(total);
        $('#todo-tasks').text(todo);
        $('#progress-tasks').text(progress);
        $('#done-tasks').text(done);
        
        // Update kanban counts
        $('#todo-count').text(todo);
        $('#progress-count').text(progress);
        $('#done-count').text(done);
        
        $('#empty-state').toggle(total === 0);
    }

    // INITIALIZE
    updateStats();
    console.log('✅ Advanced modal.js loaded successfully');
});


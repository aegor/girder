/**
 * This widget shows a list of metadata in a given item.
 */
girder.views.MetadataWidget = girder.View.extend({
    events: {
        'click .g-item-metadata-add-button': 'addMetadata',
        'click .g-item-metadata-edit-button': 'editMetadata'
    },

    addMetadata: function () {
        var newRow = $('<div>').attr({
            class: 'g-item-metadata-row editing'
        }).appendTo(this.$el.find('.g-item-metadata-container'));
        this.metadatumEditWidget = new girder.views.MetadatumEditWidget({
            el: newRow,
            item: this.item,
            key: '',
            value: '',
            girder: girder
        });
    },

    editMetadata: function (event) {
        var row = $(event.currentTarget.parentElement);
        row.addClass('editing').html('');
        this.metadatumEditWidget = new girder.views.MetadatumEditWidget({
            el: row,
            item: this.item,
            key: row.attr('g-key'),
            value: row.attr('g-value'),
            girder: girder
        });
    },

    initialize: function (settings) {
        this.item = settings.item;
        this.item.on('g:changed', function () {
            this.render();
        }, this);
        this.render();
    },

    render: function () {
        this.$el.html(jade.templates.metadataWidget({
            item: this.item,
            girder: girder
        }));

        return this;
    }

});

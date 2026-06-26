from PySide6.QtCore import Qt, QAbstractListModel, QModelIndex, Signal


class EntryListModel(QAbstractListModel):
    def __init__(self, entries=None):
        super().__init__()
        self._entries = entries or []

    def rowCount(self, parent=QModelIndex()):
        return len(self._entries)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        e = self._entries[index.row()]
        if role == Qt.DisplayRole:
            preview = e.quote[:80].replace('\n', ' ')
            return preview
        if role == Qt.UserRole:
            return e
        return None

    def entry_at(self, row):
        if 0 <= row < len(self._entries):
            return self._entries[row]
        return None

    def set_entries(self, entries):
        self.beginResetModel()
        self._entries = entries
        self.endResetModel()

    def add_entry(self, entry):
        self.beginInsertRows(QModelIndex(), len(self._entries), len(self._entries))
        self._entries.append(entry)
        self.endInsertRows()

    def update_entry(self, row, entry):
        self._entries[row] = entry
        self.dataChanged.emit(self.index(row), self.index(row))

    def remove_entry(self, row):
        self.beginRemoveRows(QModelIndex(), row, row)
        del self._entries[row]
        self.endRemoveRows()

    def entries(self):
        return self._entries

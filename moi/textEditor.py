from abc import ABC, abstractmethod
import logging
from pprint import pformat
import copy


"""
When inserting a new character, all *shape* items may need to
be updated (shift). Observer pattern.


Indexing techniques:
(i,j)
f'{line}.{column}'

The line ending characters : '\n', '\r', '\r\n'  ...
SEE str.splitlines(keepends = False) and the list of *line boundaries*.
Terminators.

(i, length)

Keeping in mind the null tag problem when cutting tags...

There are three cases.
1) The affected tag becomes empty and it was the only tag.
1) The cursor points at the beginning of a tag.
2) The cursor points at the middle of a tag. When the cursor
points at the ending char. of a tag, this char. can't be
affected by a normal deletion.
3) The cursor points at the end of the text (virtual char.).

An alternative to *_get_pos_tag* could utilize the double linked
tag list structure.

Any edition function should return a delta object to manage
*undo*/*redo* operations and to allow incremental change of
the GUI structure (instead of a complete reloading).

Font kerning. Antialiasing.

The Free Type Project library.

"""

class TextEditor:


    def __init__(self,
                 TextFormatter,
                 tag_list = None,
                 text = None):

        # Mutable values of default parameters are evaluated only once.
        tag_list = None if tag_list is None else tag_list
        text = '' if text is None else text
        self._current_format = TextFormatter.DEFAULT_FORMAT
        self._incremental_format = TextFormatter.DEFAULT_FORMAT
        self.cursor_pos = -1
        self.tag_id = None
        self.text = text
        self.tags = Tags(tag_list)

        self.Formatter = TextFormatter

        
        logging.getLogger('text_editor').debug(
            '*************\n'
            'NEW INSTANCE\n'
            '*************\n'
        )



    @property
    def current_format(self):
        """
        Association with a GUI.
        """
        return self._current_format


    @current_format.setter
    def current_format(self, value):
        new_format = self.Formatter.merge(self.current_format,
                                          value)
        self._current_format = new_format
        #
        logging.getLogger('text_editor').debug(
            'new format\n'
            f'old format\n{str(self._current_format)}\n'
            f'new format\n{str(new_format)}')

        

    @property
    def incremental_format(self):
        """
        Association with a GUI.
        """
        return self._incremental_format


    @incremental_format.setter
    def incremental_format(self, value):
        self._incremental_format = value
        #
        logging.getLogger('text_editor').debug(
            'new incremental format\n'
            f'{value}')


    def edit(self, s):
        """
        A new tag is created for any new inserted string.
        Edits are normally made one character at a time.
        Copying and pasting...
        *s* is inserted before the character pointed by
        *cursor_pos*.
        >>> t = 'abc'
        >>> pos = len(t)
        >>> t = t[:len(t)] + 'd' + t[len(t):]
        >>> t[pos]
        'd'
        """
        #
        new_tag = [len(s), self.current_format]
        #
        # Three cases.
        # 1) The text was empty. The editor structure needs to be
        # initialized.
        if self.text == '':
            assert self.cursor_pos == -1
            assert self.tag_id == None
            self.text = (self.text[:0] +
                         s +
                         self.text[0:])
            # len(s) + 1 for moving the cursor AFTER the last
            # inserted character (virtual char.).
            self.cursor_pos += len(s) + 1
            self.tag_id = self.tags.create(new_tag,
                                           None)
        else:
            self._cut_tag(self.cursor_pos)
            # Even if self.cursor_pos == len(self.text) (virtual char.).
            self.text = (self.text[:self.cursor_pos] +
                         s +
                         self.text[self.cursor_pos:])
            self.cursor_pos += len(s)
            # 2) Insertion at the beginning.
            if self.cursor_pos == len(s):
                self.tag_id = self.tags.create(new_tag,
                                               None)
            # 3) Insertion at the middle or at the end.
            else:
                self.tag_id = self.tags.create(new_tag,
                                               self.tag_id)
        
        self._merge_tag_on_both_sides(self.tag_id)

        logging.getLogger('text_editor').debug(
            f'edit\n'
            f'new string {s}'
            f'{str(self)}')


    def delete(self):
        """
        The *curent_format* is still the same after multiple *delete()*
        calls in a row.
        If the cursor points at the beginning of a tag. This tag
        remains the same.
        """
        if self.cursor_pos >= 1:
            # Obvious condition.
            self.text = (self.text[:(self.cursor_pos - 1)] +
                         self.text[self.cursor_pos:])
            # tag_id MAY be different from self.tag_id (current tag).
            tag_id, tag, _ = self._get_pos_tag(self.cursor_pos - 1)
            tag[0] -= 1
            self.cursor_pos -= 1
            if tag[0] == 0:
                # An empty tag has appeared.
                prev_tag_id =  self.tags.previous(tag_id)
                self.tags.delete(tag_id)
                if not prev_tag_id == tag_id:
                    # There is a tag before the deleted tag.
                    if self.tag_id == tag_id:
                        assert self.cursor_pos == len(self.text)
                        self.tag_id = prev_tag_id
                    self._merge_tag(prev_tag_id)
                elif self.text == '':
                    assert self.tags.counter == 0
                    # This setting of *cursor_pos* is necessary because
                    # of the ending virtual character.
                    self.cursor_pos = -1
                    self.tag_id = None
                else:
                    # There is no tags before the deleted tag but
                    # there is a tag after it. The successor tag
                    # contains the cursor.
                    pass
                    
            
        logging.getLogger('text_editor').debug(
            f'delete\n'
            f'{str(self)}')


    def change_position(self, pos):
        """
        When the cursor is moved without changing the text
        (keyboard and mouse actions), the *current_format*
        has to reflect the format pointed by the cursor.
        The text ending position (len(self.text)) is special
        because the cursor points at a virtual character in this case.
        """
        self._check_pos(pos)
        self.cursor_pos = pos
        if pos == len(self.text):
            if len(self.text) > 0:
                self.tag_id, tag, _ = self._get_pos_tag(pos - 1)
                self.current_format = tag[1]
        else:
            self.tag_id, tag, _ = self._get_pos_tag(pos)
            self.current_format = tag[1]

        logging.getLogger('text_editor').debug(
            f'change_position {pos}\n'
            f'{str(self)}')

    

    def delete_selection(self, i, j):
        """
        To delete a substring from the position i (included)
        to j (excluded).
        Positions are zero-based indices.
        The function is equivalent to multiple calls to *delete*.
        >>> t = 'abc'
        >>> t[:0]+t[len(t):]
        ''
        >>> t[:1]+t[2:]
        'ac'
        """
        self._check_range(i, j)
        self._scan_and_process_tags(i, j, 
                                    self._delete_tag)
        self.text = (self.text[:i] +
                     self.text[j:])
        if self.text == '':
            self.cursor_pos = -1
            self.tag_id = None
        else:
            # Even if i == len(self.text).
            self.change_position(i)
            # self.tag_id is updated by *change_position*.
            tag_id = self.tags.previous(self.tag_id)
            # Even if tag_id == self.tag_id.
            self._merge_tag_on_both_sides(self.tag_id)
            
        logging.getLogger('text_editor').debug(
            f'delete_selection {i}, {j}\n'
            f'{str(self)}')


    def change_selection_format(self, i, j):
        """
        To change the format of a substring (selection).
        From i (included) to j (excluded).
        """
        self._check_range(i, j)
        self._scan_and_process_tags(i, j,
                                    self._update_tag_format,
                                    self._merge_tag_on_both_sides)
        self.change_position(i)

        logging.getLogger('text_editor').debug(
            f'change_selection_format {i}, {j}\n'
            f'{str(self)}')

        
    def compile(self, display_cursor = False):
        """ '\u2588' stands for the insertion cursor. """
        repr = []
        i = 0
        for tag in self.tags.all:
            if display_cursor and i <= self.cursor_pos < i + tag[0]:
                repr.append(
                    (self.text[i:self.cursor_pos] +
                     '\u2588' +
                     self.text[self.cursor_pos:(i+tag[0])], tag[1]))
            else:
                repr.append(
                    (self.text[i:(i+tag[0])], tag[1]))
            i += tag[0]
        if display_cursor and self.cursor_pos == len(self.text):
            if not repr == []:
                token = repr.pop(-1)
                repr.append((token[0]+'\u2588', token[1]))
            else:
                repr.append(('\u2588', self.current_format))
        return repr

    
    @staticmethod
    def pos_to_line_column(s,
                           i,
                           line_base = 1,
                           column_base = 0):
        """
        i is alowed to be len(s) (the 'x' additional character).
        Line ending groups are always included for obvious reasons.
        """
        if not -1 <= i <= len(s):
            raise IndexError()
        if i == -1:
            return (line_base, column_base)
        s = s + 'x'
        lines = s.splitlines(keepends = True)
        line_nb = 0
        counter = 0
        next_value = len(lines[line_nb])
        while next_value <= i:
            line_nb += 1
            counter = next_value
            next_value += len(lines[line_nb])
        return (line_nb + line_base,
                i - counter + column_base)


    @staticmethod 
    def line_column_to_pos(s,
                           line_nb,
                           column,
                           keepends = False,
                           line_base = 1,
                           column_base = 0,
                           strict = False,
                           line_is_important = False):
        """
        Keys (up, down, left, right).

        This function is fault-tolerant. Line boundaries can
        be crossed.

        An extra char. is added at the end because the cursor
        can point at the position just after the last character.
        
        *splitlines* doesn't return a final empty line when
        the last group is a line ending group. This is the other
        reason why 'x' is inserted.
        """
        s = s + 'x'
        lines = s.splitlines(keepends = keepends)
        # To remove 'x'.
        last_line = lines.pop()
        lines.append(last_line[:len(last_line)-1])
        # A line can be empty.
        line_nb -= line_base
        column -= column_base
        if strict:
            if (not 0 <= line_nb <= len(lines) - 1 or
                not 0 <= column <= len(lines[line_nb])):
                #
                raise IndexError()
        else:
            if line_nb > len(lines) - 1:
                line_nb = len(lines) - 1
            if line_nb < 0:
                line_nb = 0

            if line_is_important:
                column = min(len(lines[line_nb]),
                             max(0, column))
            else:
                if column < 0:
                    while column < 0 and line_nb > 0:
                        line_nb -= 1
                        column = len(lines[line_nb]) + 1 + column
                    if column < 0:
                        column = 0
                while column > len(lines[line_nb]):
                    if line_nb < len(lines) - 1:
                        column -= len(lines[line_nb]) + 1
                        line_nb += 1
                    elif line_nb == len(lines) - 1:
                        column = len(lines[line_nb])

        if not keepends:
            lines = s.splitlines(keepends = True)
            
        i = sum([len(lines[i]) for i in range(line_nb)]) + column
        return i
    
 
    def _scan_and_process_tags(self, i, j, *functions):
        """
        From i (included) to j (excluded).
        The given functions has to accept two arguments.
        *_update_tag_format*
        *_merge_tag_on_both_sides*
        *_delete_tag*
        """
        self._check_range(i, j)
        
        # Cutting overlapping tags.
        self._cut_tag(i)
        self._cut_tag(j)  
        # Selecting tags between i and j.
        selected_tags = self._select_tags(i, j)
        deleted_tags = set()
        #
        logging.getLogger('text_editor').debug(
            f'scan_and_process_tags {i}, {j}\n'
            f'selected_tags {selected_tags}\n'
            f'functions to apply\n'
            f'{[f.__name__ for f in functions]}\n'
            f'{str(self)}')


        for tag_id in selected_tags:
            # Processing each selected tag if it still exists.
            for func in functions:
                if not tag_id in deleted_tags:
                    func(tag_id, deleted_tags)
                    #
                    logging.getLogger('text_editor').debug(
                        f'{func.__name__} {tag_id}\n'
                        f'deleted tags {deleted_tags}\n'
                        f'{str(self)}')


    def _get_pos_tag(self, pos):
        """
        To get data about a positional tag. 
        
        The tag counters have to be adapted to the text
        zero-based index.
        The third returned value is the index of the first
        character associated with the wanted tag.
        This function interprets tags.
        """
        tag_id = self.tags.root
        tag = self.tags[tag_id]
        counter = -1
        while counter + tag[0] < pos:
            counter += tag[0]
            tag_id = self.tags.next(tag_id)
            tag = self.tags[tag_id]
        
        return (tag_id,
                tag,
                counter + 1)

               

    def _cut_tag(self, i):
        """
        If there is not a tag which starts at the position i in
        the *text*, a new one is created which does.
        The old one is truncated.
        """
        self._check_pos(i)
        # The final character (len(self.text)) is virtual. Therefore, it
        # belongs to no tags.
        if i < len(self.text):
            tag_id, tag, start_pos = self._get_pos_tag(i)
            if not start_pos == i:
                old_length = tag[0]
                new_length = i - start_pos
                tag[0] = new_length
                self.tags.create([old_length - new_length, tag[1]],
                                 tag_id)
                return True
        return False



    def _select_tags(self, i, j):
        """
        To find the tags between the positions i and j,
        The tags are identified by get their indices.

        From i (included) and j (excluded).
        """
        selected_tags = []
        start_id, _, _ = self._get_pos_tag(i)
        end_id = start_id
        if j > i + 1:
            # j - 1 because j is excluded.
            end_id, _, _ = self._get_pos_tag(j - 1)
        selected_tags.append(start_id)
        current_id = start_id
        while not current_id == end_id:
            current_id = self.tags.next(current_id)
            selected_tags.append(current_id)
        return selected_tags


    def _update_tag_format(self,
                           tag_id,
                           deleted_tags = None):
        """
        *tag* is a pointer to an item in the container *tags*.
        The Formatter method can do subtle format conversions.
        The *current_format* is used.
        """
        if self.incremental_format is not None:
            tag = self.tags[tag_id]
            new_format = self.Formatter.merge(tag[1],
                                              self.incremental_format)
            tag[1] = new_format



    def _merge_tag_on_both_sides(self,
                                 tag_id,
                                 deleted_tags = None):
        mergers = [False, False]
        prev_tag_id = self.tags.previous(tag_id)
        next_tag_id  = self.tags.next(tag_id)
        if next_tag_id is not None:
            # 0n the right.
            if self._merge_tag(tag_id):
                mergers[1] = True
                if deleted_tags is not None:
                    deleted_tags.add(next_tag_id)

        if prev_tag_id is not None:
            # On the left.
            if self._merge_tag(prev_tag_id):
                mergers[0] = True
                if deleted_tags is not None:
                    deleted_tags.add(tag_id)
        return mergers


    def _merge_tag(self, left_tag_id):
        """
        If the merger is possible, the right tag is merged into
        the left one and deleted.
        *self.tag_id* (current tag) is updated if necessary.
        """
        left_tag = self.tags[left_tag_id]
        right_tag_id = self.tags.next(left_tag_id)
        
        if right_tag_id is not None:
            right_tag = self.tags[right_tag_id]
            if self.Formatter.compare(left_tag[1], right_tag[1]):
                #
                left_tag[0] += right_tag[0]
                self.tags.delete(right_tag_id)
                if self.tag_id == right_tag_id:
                    self.tag_id = left_tag_id
                return True
        return False


    def _delete_tag(self, tag_id, deleted_tags):
        deleted_tags.add(tag_id)
        self.tags.delete(tag_id)
    
    
    def _check_pos(self, pos):
       if not 0 <= pos <= len(self.text):
            raise IndexError('Wrong position.') 

    
    def _check_range(self, i, j):
        if not 0 <= i or not i < j <= len(self.text):
            raise ValueError('Range error.')

    
    def __repr__(self):
        repr = self.compile(display_cursor = True)
        text = (
            f'cursor_pos {self.cursor_pos}\n'
            f'current tag id {self.tag_id}\n'
            f'current_format\n{self._current_format}\n'
            f'{pformat(repr)}')
        return text




class AbstractTagList:
    

    @abstractmethod
    def __init__(self, a_list = None):
        pass


    @abstractmethod
    def __getitem__(self, arg):
        pass


    @abstractmethod
    def delete(self, i):
        pass


    @abstractmethod
    def create(self, new_tag):
        pass


    @abstractmethod
    def next(self, i):
        pass

    
    @abstractmethod
    def previous(self, i):
        pass



    
class Tags(AbstractTagList):
    
    
    def __init__(self, a_list = None):
        """
        The structure is based on three dynamic arrays.
        The root is the only tag such as its precursor is itself.
        The None value is reserved. The new tag's value can't be None.
        """
        self._reset(a_list)


    def _reset(self, a_list = None):
        if a_list is not None:
            self._tags = copy.deepcopy(a_list)
            self._length = len(self._tags)
            self.counter = self._length
            self._succ = list(range(1, self.counter)) + [None]
            self._prec = [None] + list(range(0, self.counter - 1))
            self._next_id = self.counter
            self.root = 0
        else:
            # The initialization is delicate.
            self._tags = []
            self._length = 0
            self.counter = 0
            self._succ = []
            self._prec = []
            self._next_id = 0
            self.root = None


    def __getitem__(self, arg):
        return self._tags.__getitem__(arg)
            
    
    def create(self, new_tag, precursor_id):
        """
        The id of the new item is returned. This function depends from
        *_insert_tag*.
        """
        assert new_tag is not None
        new_id = self._next_id
        if new_id == self._length:
            # The underlying arrays are too small and need to be resized.
            assert self.counter == self._length
            self._tags.append(new_tag)
            self._succ.append(None)
            self._prec.append(None)
            # Insertion.
            self._insert_tag(new_id,
                             precursor_id)
            self._length += 1
            self._next_id = self._length
        else:
            # There is room for the new item.
            self._tags[new_id] = new_tag
            # Insertion.
            self._insert_tag(new_id,
                             precursor_id)
            self._next_id = self._find_available_place()
        self.counter += 1
        # Reduction of the underlying arrays
        # if they are too large.
        if self.counter < self._length / 100:
            self._reset(self.all)
        #
        logging.getLogger('tags').debug(
            'create\n'
            f'new_tag {new_tag}\n'
            f'precursor {precursor_id}\n'
            f'{str(self)}')
        return new_id


    def _find_available_place(self):
        for i, tag in enumerate(self._tags):
                if tag is None:
                    return i
        return self._length

    
    def _insert_tag(self, new_tag_id, precursor_id):
        """
        Redefining self._succ[new_tag_id] and
        self._prec[new_tag_id].
        """
        # Two cases.
        if precursor_id is None:
            # 1) Insertion at the beginning. New root (no precursors).
            if self.root is None:
                assert self.counter == 0
                self._succ[new_tag_id] = None
            else:
                self._succ[new_tag_id] = self.root
                self._prec[self.root] = new_tag_id
            # Root property.
            self._prec[new_tag_id] = new_tag_id
            self.root = new_tag_id
        else:
            # 2) Insertion in the middle or at the end. There is a
            # precursor.
            successor_id = self._succ[precursor_id]
            self._prec[new_tag_id] = precursor_id
            self._succ[precursor_id] = new_tag_id
            #
            if successor_id is not None:
                self._prec[successor_id] = new_tag_id
                self._succ[new_tag_id] = successor_id
            else:
                # Insertion at the end.
                self._succ[new_tag_id] = None
      
            
    def delete(self, tag_id):
        """
        There is no need to set self._succ[tag_id]
        and self._prec[tag_id] to None.
        """
        successor_id = self._succ[tag_id]
        precursor_id = self._prec[tag_id]
        self._tags[tag_id] = None
        # A new place is available.
        self._next_id = tag_id
        # Two cases.
        # 1) Deletion of the root.
        if tag_id == precursor_id:
            if successor_id is not None:
                self.root = successor_id
                self._prec[successor_id] =  successor_id
                self.counter -= 1
            else:
                # The root was the only tag left.
                assert self.counter == 1
                # *_reset* sets self.counter appropriately.
                self._reset()
        # 2) Deletion of a normal item. All tags have a distinct precursor
        # except the root.
        else:
            assert precursor_id is not None
            if successor_id is not None:
                # Deletion in the middle.
                self._succ[precursor_id] = successor_id
                self._prec[successor_id] = precursor_id
                
            else:
                # Deletion at the end.
                self._succ[precursor_id] = None
            self.counter -= 1
        logging.getLogger('tags').debug(
            f'delete {tag_id}\n'
            f'{str(self)}')
        


    def next(self, tag_id):
        i = self._succ[tag_id]
        return i


    def previous(self, tag_id):
        i = self._prec[tag_id]
        return i
        
        
 
    @property
    def all(self):
        tags = []
        if self.root is not None:
            i = self.root
            tags.append(self._tags[i])
            # Against a possible infinite loop
            k = 0
            while self._succ[i] is not None and k < self._length:
                i = self._succ[i]
                tags.append(self._tags[i])
                k += 1
            if k > self._length:
                raise Exception('Broken successor list (infinite loop).')
        return tags

    
    def __repr__(self):
        hashed_tags = [id(t) for t in self._tags]
        return (f'tags\n{hashed_tags}\n'
                f'succ\n{self._succ}\n'
                f'prec\n{self._prec}\n'
                f'root {self.root}\n'
                f'counter {self.counter}\n'
                f'_next_id {self._next_id}\n'
                f'_length {self._length}')
        

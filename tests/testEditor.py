import unittest
import logging
from moi.textEditor import *
from pprint import pformat


class Formatter:
    DEFAULT_FORMAT = 'default'
    
    @staticmethod 
    def merge(old, new):
        return new

    @staticmethod 
    def compare(format_one, format_two):
        return format_one == format_two



class TestEditor(unittest.TestCase):

    def setUp(self):
        self.s = 'Bla bla blabla.'



    def test_Tags(self):       
        tags = Tags([[1,'a'], [2, 'b'], [3, 'c']])
        self.assertEqual(tags.counter, 3)
        # Insertion at the beginning.
        tags.create([4, 'd'], None)
        self.assertEqual(tags.counter, 4)
        self.assertEqual(tags.all,
                         [[4, 'd'], [1,'a'], [2, 'b'], [3, 'c']])
        self.assertEqual(tags._next_id, 4)
        # Deletion of a tag in the middle.
        second_tag_id = tags.next(tags.root)
        tags.delete(second_tag_id)
        self.assertEqual(tags.all,
                         [[4, 'd'], [2, 'b'], [3, 'c']])
        self.assertEqual(tags._next_id, 0)
        # Insertion in the middle.
        tag_object = [5, 'e']
        tags.create(tag_object, tags.root)
        self.assertEqual(tags.all,
                         [[4, 'd'], tag_object, [2, 'b'], [3, 'c']])
        # Deletion of the root.
        tags.delete(tags.root)
        self.assertEqual(tags[tags.root], tag_object)
        self.assertEqual(tags.all,
                         [tag_object, [2, 'b'], [3, 'c']])
        # Another deletion in the middle.
        second_tag_id = tags.next(tags.root)
        tag = tags[second_tag_id]
        self.assertEqual(tag, [2, 'b'])
        tags.create([6, 'f'], second_tag_id)
        #
        self.assertEqual(tags.all,
                         [tag_object, [2, 'b'], [6, 'f'], [3, 'c']])
        # Reset.
        tags._reset(tags.all)
        self.assertEqual(tags._tags,
                         [tag_object, [2, 'b'], [6, 'f'], [3, 'c']])
        ##############################################################
        tags = Tags()
        tags.create([1, 'alpha'], None)
        tags.create([2, 'beta'], tags.root)
        self.assertEqual(tags.all, [[1, 'alpha'], [2, 'beta']])
        #
        tags.delete(tags.next(tags.root))
        self.assertEqual(tags.all, [[1, 'alpha']])
        #
        tags.delete(tags.root)
        self.assertEqual(tags.all, [])
        ##############################################################
        some_tags = list(range(1000))
        tags = Tags()
        an_id = None
        for tag in some_tags:
            an_id = tags.create(tag, an_id)
        for _ in range(500):
            an_id = tags.previous(an_id)
        self.assertEqual(tags[an_id], 999 - 500)
        
    
    def test_get_pos_tag(self):
        editor = TextEditor(Formatter,
                            tag_list = [[2,'1'],[4, '2'], [8, '3']])

        self.assertEqual(editor._get_pos_tag(2),
                         (1, [4, '2'], 2))
        self.assertEqual(editor._get_pos_tag(5),
                         (1, [4, '2'], 2))
        self.assertEqual(editor._get_pos_tag(6),
                         (2, [8, '3'], 6))
        self.assertEqual(editor._get_pos_tag(13),
                         (2, [8, '3'], 6))
    

    def test_merge_tags_True(self):
        editor = TextEditor(Formatter,
                            tag_list = [[2,'1'], [4, '2'], [8, '2']])
        result = editor._merge_tag(1)
        self.assertEqual(editor.tags.all,
                         [[2, '1'], [12, '2']])
        self.assertEqual(result, True)
    

    def test_merge_tags_False(self):
        editor = TextEditor(Formatter,
                            tag_list = [[2,'1'], [4, '2'], [8, '2']])
        result = editor._merge_tag(0)
        self.assertEqual(editor.tags.all,
                         [[2,'1'], [4, '2'], [8, '2']])
        self.assertEqual(result, False)


    def test_cut_tag(self):
        editor = TextEditor(Formatter)
        editor.current_format = 'X'
        editor.edit(10*'a')
        editor._cut_tag(2)
        editor._cut_tag(8)
        editor._cut_tag(10)
        self.assertEqual(editor.tags.all,
                         [[2, 'X'],
                          [6, 'X'],
                          [2, 'X']])
        
    

    def test_merge_tag_on_both_sides(self):
        editor = TextEditor(Formatter,
                            tag_list = [[2,'7'], [4, '7'], [8, '7']])
        result = editor._merge_tag_on_both_sides(1)
        self.assertEqual(editor.tags.all,
                         [[14, '7']])
        self.assertEqual(result,
                         [True, True])


    def test_update_tag_format(self):
        editor = TextEditor(Formatter,
                            tag_list = [[2,'7'], [4, '7'], [8, '7']])
        editor.incremental_format = 'new'
        editor._update_tag_format(1)
        self.assertEqual(editor.tags.all[1],
                         [4, 'new'])


    def test_select_tags(self):
        editor = TextEditor(Formatter,
                            tag_list = [[2,'7'], [4, '7'], [8, '7']])
        def make(indices):
            return [editor.tags[i] for i in indices]
        indices = editor._select_tags(1, 10)
        self.assertEqual(make(indices),
                         [[2,'7'], [4, '7'], [8, '7']])
        #
        indices = editor._select_tags(2, 7)
        self.assertEqual(make(indices),
                         [[4, '7'], [8, '7']])
        #
        indices = editor._select_tags(2, 3)
        self.assertEqual(make(indices), [[4, '7']])




    def test_simple_edits(self):
        editor = TextEditor(Formatter)

        for c in self.s:
            editor.edit(c)
        self.assertEqual(editor.text, self.s)
        self.assertEqual(editor.tags.all,
                         [[len(self.s), 'default']])


    def test_edits_and_deletions(self):
        editor = TextEditor(Formatter)
        for s in ['a', 'b', None, 'c', 'd', None, 'e']:
            if s is None:
                editor.delete()
            else:
                editor.edit(s)
        self.assertEqual(editor.text, 'ace')
        self.assertEqual(editor.tags.all,
                         [[3, 'default']])
               
        for i in range(3):
            editor.delete()

        self.assertEqual(editor.text, '')
        self.assertEqual(editor.cursor_pos, -1)
        self.assertEqual(editor.tag_id, None)

        editor.edit('A')
        self.assertEqual(editor.text, 'A')
        self.assertEqual(editor.tags.all,
                         [[1, 'default']])

    

    def test_change_selection_format(self):
        # There is an imortant but subtle distinction between
        # *current_format* and *incremental_format*
        editor = TextEditor(Formatter)
        editor.current_format = 'B'
        editor.edit('black')
        editor.edit(' ')
        editor.delete()
        editor.current_format = 'N'
        editor.edit('blabla')
        editor.current_format = 'I'
        editor.edit('italic')

        self.assertEqual(editor.tags.all,
                         [[5, 'B'],
                          [6, 'N'],
                          [6, 'I']])

        editor.incremental_format = 'X'
        editor.change_selection_format(0, 8)
        self.assertEqual(editor.tags.all,
                         [[8, 'X'],
                          [3, 'N'],
                          [6, 'I']])


    def test_repr(self):
        """
        SEE __repr__.
        """
        editor = TextEditor(Formatter)
        rich_text = [('The ', '1'), ('world ', '2'),
                     ('is ', '3'), ('mine.', '4')]
        for token in rich_text:
            editor.current_format = token[1]
            editor.edit(token[0])
        self.assertEqual(pformat(rich_text),
                         str(editor.compile()))
    

    def test_change_position(self):
        editor = TextEditor(Formatter)
        rich_text = [('The ', '1'), ('world ', '2'),
                     ('is ', '3'), ('mine.', '4')]
        for token in rich_text:
            editor.current_format = token[1]
            editor.edit(token[0])
        #
        editor.change_position(4)
        self.assertEqual(editor.current_format, '2')
        self.assertEqual(editor.cursor_pos, 4)
        self.assertEqual(editor.tags[editor.tag_id],
                         [6, '2'])


    def test_complex_interactions(self):
        editor = TextEditor(Formatter)
        complex_interact = [
            ('This is a very interesting', '1', True),
            (' project. ', 'X', True),
            ('The editro', '2', True),
            ('##', '', False),
            ('or is abstract.', '3', True)]
        for action in complex_interact:
            if action[2]:
                editor.current_format = action[1]
                for c in action[0]:
                    editor.edit(c)
            else:
                for _ in action[0]:
                    editor.delete()
        editor.current_format = 'X'
        editor.change_selection_format(10, 26)

        
    def test_line_column_to_pos(self):
        """
        This\r\n
        is\n
        \n
        the\n
        source\n
        code.
        """
        editor = TextEditor(Formatter)
        s = 'This\r\nis\n\nthe\nsource\ncode.'
        editor.edit(s)
        
        def f(line, column, dic = None):
            dic = {} if dic is None else dic
            return editor.line_column_to_pos(s, line, column, **dic)
        
        self.assertEqual(s[f(1,0)], 'T')
        self.assertEqual(s[f(0,0, {'line_base' : 0})], 'T')
        self.assertEqual(s[f(2,0)], 'i')
        self.assertEqual(s[f(2,1)], 's')
        # '\n\n' counts for two line ending groups.
        self.assertEqual(s[f(3,0)], '\n') 
        # When the conversion is not strict,
        # the function interprets the column argument
        # as a relative distance to a certain position.
        self.assertEqual(s[f(1,5)], 'i')
        with self.assertRaises(IndexError):
            _ = f(1,5, {'strict' : True})        
        # '\r\n' is a line ending group like '\n'.
        self.assertEqual(s[f(1,5, {'keepends' : True,
                                   'strict' : True})],
                         '\n')
        self.assertEqual(s[f(1,6, {'keepends' : True,
                                   'strict' : True})],
                         'i')
        with self.assertRaises(IndexError):
            _ = f(1,7, {'keepends' : True,
                        'strict' : True})
        # Two ways to point at the same character.
        self.assertEqual(s[f(1,7, {'keepends' : True})],
                         'i')
        self.assertEqual(s[f(2,0, {'keepends' : True,
                                   'strict' : True})],
                         'i')
        #
        self.assertEqual(s[f(1,6)], 's')
        # After the last character.
        self.assertEqual(f(1,100), len(s))
        self.assertEqual(f(6, 5, {'strict' : True}), len(s))
        #
        self.assertEqual(s[f(6,-4)], 'r')
        self.assertEqual(s[f(6,-5)], 'u')
        self.assertEqual(s[f(6,-100)], 'T')

        
    def test_pos_to_line_column(self):
        """
        g is the inverse function of f if the conversion is *strict*.
        """
        editor = TextEditor(Formatter)
        s = 'This\r\nis\n\nthe\nsource\ncode.'
        editor.edit(s)
        
        def f(line, column, dic = None):
            dic = {} if dic is None else dic
            return editor.line_column_to_pos(s, line, column, **dic)

        def g(pos, dic = None):
            dic = {} if dic is None else dic
            return editor.pos_to_line_column(s, pos, **dic)
        #
        self.assertEqual(g(f(1,0, {'strict' : True}),
                           {} ), (1,0))

        self.assertEqual(g(f(2,0, {'strict' : True}),
                           {} ), (2,0))
        
        self.assertEqual(g(f(2,1, {'strict' : True}),
                           {} ), (2,1))
        
        self.assertEqual(g(f(4,2, {'strict' : True}),
                           {} ), (4,2))

        # If the conversion is not *strict*.
        self.assertEqual(g(f(1,4, {'strict' : True}),
                           {} ), (1,4))
        self.assertEqual(g(f(1,5, {}),
                           {} ), (2,0))
        #
        self.assertEqual(TextEditor.pos_to_line_column('a',
                                                        1),
                         (1, 1))
        self.assertEqual(TextEditor.pos_to_line_column('a\n',
                                                        2),
                         (2, 0))
        self.assertEqual(g(f(6,5, {'strict' : True}),
                           {} ), (6,5))
        

    def tearDown(self):
        pass

# TO TEST

# Changing the selection's format of (2, 6) in 'nnnBBnnn'.

# Changing the selection's format of (3, 5) in 'nnnBBnnn'
# (the upper bound is excluded and formats are implicit).

# Inserting a new char at the beginning of the text with
# a new format.

if __name__ == '__main__':
    
    def suite(test_names):
        suite = unittest.TestSuite()
        for name in test_names:
            suite.addTest(TestEditor(name))
        return suite

    runner = unittest.TextTestRunner()
    #runner.run(suite(['test_complex_interactions']))


    unittest.main()


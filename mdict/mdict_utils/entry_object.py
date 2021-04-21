class EntryObject:
    def __init__(self, m_name, m_entry, m_record, m_pror, pk, f_pk, p1, p2, extra=''):
        self.mdx_name = m_name
        self.mdx_entry = m_entry
        self.mdx_record = m_record
        self.mdx_pror = m_pror
        self.pk = pk
        self.f_pk = f_pk  # f_pk,f_p1,f_p2是该词条最终指向（LINK）的词条所在词典的id，以及位置p1,p2
        self.f_p1 = p1
        self.f_p2 = p2
        self.extra = extra
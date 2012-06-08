import string
import sys
from bs4 import BeautifulSoup,Comment,NavigableString,CData

__DEBUG_OUTPUT__=False
HTML_STOP_TAG={"textarea":1,"iframe":1,"script":1,"input":1,"style":1}
HTML_H_TAG={"h1":0,"h2":0,"h3":0,"h4":0,"h5":0,"h6":0}
HTML_CONTENT_SUBTAG={"p":1,"br":1,"b":1,"strong":1,"hr":1,"pre":1,"blockquote":1}


class ExtractHtml:
    def __init__(self, doc , DEBUG=False):
        global __DEBUG_OUTPUT__
        '''Constructor:'''
        '''@doc : original html document(coding utf8)'''
        '''@return : class itself'''
        __DEBUG_OUTPUT__=DEBUG
        self.__result_dict={"STATE":"False","title":"","content":"","comment":"","summary":""}
        self.__coding="utf8"
        self.__parser="html5lib"
        self.__density=0.5
        self.__content_density=0.5
        self.__soup=None
        self.__H_TAG_MAX_NUM=5
        
        self.__beautifulsoup(doc)

    def __is_empty_tag(self,tag,special_name_dict=None):
        if isinstance(tag,NavigableString):
            if len(tag.rstrip().strip())==0:
                return True
            else:
                return False
        state=False
        if self.__has_children(tag):
            if len(tag.contents)==0:
                state=True
            if len(tag.contents)==1:
                if isinstance(tag.contents[0],NavigableString):
                    if len(tag.contents[0].rstrip().strip())==0:
                        state=True
        if special_name_dict!=None:
            if tag.name not in special_name_dict:
                state=False
        return state

    def __head_tail_normalization(self,content_tag):
        if self.__has_children(content_tag):
            children=content_tag.contents
            lens=len(children)
            extract_candidates=[]
            if lens>0:
                for i in range(0,lens):
                    if self.__is_empty_tag(children[i],HTML_CONTENT_SUBTAG):
                        extract_candidates.append(children[i])
                    else:
                        break
                i=lens-1
                while i>=0:
                    if self.__is_empty_tag(children[i],HTML_CONTENT_SUBTAG):
                        extract_candidates.append(children[i])
                    else:
                        break
                    i-=1
                for tag in extract_candidates:
                    tag.extract()

    def __has_children(self,tag):
        try:
            tag.children
            return True
        except:
            return False

    def __judgement_parent(self,child,parent):
        if child==parent:
            return True
        if child.parent==self.__soup.body:
            return False
        return self.__judgement_parent(child.parent,parent)

    def __judgement_winner(self,winner_tag,ptag_candidate_dict):
        multi_ptag_candidate=[]
        for attrs in ptag_candidate_dict:
            for [candidate,num] in ptag_candidate_dict[attrs]:
                if num>1 and candidate!=winner_tag:
                    multi_ptag_candidate.append(candidate)
        if len(multi_ptag_candidate)==0:
            return winner_tag
        _find=False
        pwinner_tag=winner_tag.parent
        max_pnum=0
        while pwinner_tag!=self.__soup.body:
            pnum=0
            for cand in multi_ptag_candidate:
                if self.__judgement_parent(cand,pwinner_tag):
                    pnum+=1
            if pnum>max_pnum:
                max_pnum=pnum
            if pnum==len(multi_ptag_candidate):
                _find=True
                break
            pwinner_tag=pwinner_tag.parent
        return pwinner_tag
        
    def __vote_to_content_tag(self):
        content_candidate_dict={}
        ptag_candidate_dict={}
        winner_tag=None
        winner_num=0
        second_tag=None
        second_num=0
        for content_tag_name in HTML_CONTENT_SUBTAG:
            candis=list(self.__soup.body.find_all(content_tag_name))
            for tag in candis:
                candidate=tag.parent
                if candidate.name not in HTML_CONTENT_SUBTAG and tag.name=="p":
                    if str(candidate.attrs) not in ptag_candidate_dict:
                        cands_list=[]
                        cands_list.append([candidate,1])
                        ptag_candidate_dict[str(candidate.attrs)]=cands_list
                    else:
                        cand_list=ptag_candidate_dict[str(candidate.attrs)]
                        lens=len(cand_list)
                        _find=False
                        for index in range(0,lens):
                            if cand_list[index][0]==candidate:
                                cand_list[index][1]+=1
                                _find=True
                                break
                        if not _find:
                            ptag_candidate_dict[str(candidate.attrs)].append([candidate,1])
                try:
                    while candidate.name in HTML_CONTENT_SUBTAG:
                        candidate=candidate.parent
                except:
                    pass
                text_len=len(unicode(tag.get_text().replace(" ","").rstrip().strip()).encode("gbk","ignore"))
                cand_num=text_len
                if str(candidate.attrs) not in content_candidate_dict:
                    cands_list=[]
                    cands_list.append([candidate,text_len])
                    content_candidate_dict[str(candidate.attrs)]=cands_list
                else:
                    cand_list=content_candidate_dict[str(candidate.attrs)]
                    lens=len(cand_list)
                    _find=False
                    for index in range(0,lens):
                        if cand_list[index][0]==candidate:
                            cand_list[index][1]+=text_len
                            cand_num=cand_list[index][1]
                            _find=True
                            break
                    if not _find:
                        content_candidate_dict[str(candidate.attrs)].append([candidate,text_len])
                if cand_num>winner_num:
                    winner_tag=candidate
                    winner_num=cand_num
        return self.__judgement_winner(winner_tag,ptag_candidate_dict)
    
    def __extract_stop_tag(self, content_tag):
        all_tags=list(content_tag.descendants)
        parent_list=[]
        for tag in all_tags:
            if isinstance(tag,Comment) or isinstance(tag,CData):
                parent_list.append(tag.parent)
                tag.extract()
            elif isinstance(tag, NavigableString):
                continue
            else:
                if tag.name in HTML_STOP_TAG:
                    parent_list.append(tag.parent)
                    tag.extract()
        for parent in parent_list:
            if parent==None:
                continue
            if self.__is_empty_tag(parent):
                parent.extract()

    def __beautifulsoup(self,doc):
        '''using beautifulsoup parser the html doc'''
        try:
            self.__soup=BeautifulSoup(doc, self.__parser, from_encoding=self.__coding)
        except Exception,e:
            if __DEBUG_OUTPUT__:
                print >> sys.stderr,"Error: when __beautifulsoup1 - ",e
            return False
        try:
            self.__result_dict["title"]=str(self.__soup.title.next_element.encode(self.__coding)).rstrip().strip()
        except Exception,e:
            if __DEBUG_OUTPUT__:
                print >> sys.stderr,"Error: when __beautifulsoup2 title - ",e
        try:
            self.__result_dict["content"]=self.__soup.body.encode(self.__coding)
        except Exception,e:
            if __DEBUG_OUTPUT__:
                print >> sys.stderr,"Error: when __beautifulsoup2 - ",e
        self.__extract_stop_tag(self.__soup.body)
        (content_tag,succ)=(None,False)
        content_tag=self.__vote_to_content_tag()
        if content_tag==None:
            return False
        if self.__has_children(content_tag):
            self.__head_tail_normalization(content_tag)
            self.__get_summary(content_tag)
            self.__result_dict["STATE"]="True"
            self.__result_dict["content"]=unicode(content_tag).encode(self.__coding,"ignore")
        return True

    def __get_summary(self,content_tag):
        try:
            self.__result_dict["summary"]=unicode(content_tag.get_text()[:80]).encode(self.__coding,"ignore")
        except:
            pass
        
    def GetResultDict(self):
        return self.__result_dict


    


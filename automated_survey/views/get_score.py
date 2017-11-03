#questionv="What is working capital?"
#expectedansv="Working capital is the amount of a company's current assets minus the amount of its current liabilities."
#actualansv="Working capital is defined as current assets minus current liabilities."

questionv="What is bank reconciliation statement? "
expectedansv="Bank Reconciliation Statement is a statement prepared to reconcile the balances of cash book maintained by the concern and pass book maintained by the bank at periodical intervals."
actualansv="bank reconciliation statement is a banking and business activities at legal size and entities bank account with its financial records"

#questionv="What is depreciation?"
#expectedansv="Depreciation is a permanent, gradual and continuous reduction in the book value of the fixed asset."
#actualansv="Depreciation is same as loss."
#actualansv="What is depreciation?"

def getscorenew(question,expectedans,actualans):
    if expectedans and actualans:
        question = question.replace('\xa0', ' ')
        expectedans = expectedans.replace('\xa0', ' ')
        actualans = actualans.replace('\xa0', ' ')
        documents = (expectedans, actualans)
        questionwords = question.split()
        from sklearn.feature_extraction import text
        stop_words_new = text.ENGLISH_STOP_WORDS.union(questionwords)
        from sklearn.feature_extraction.text import TfidfVectorizer
        tfidf_vectorizer = TfidfVectorizer(stop_words=stop_words_new)
        tfidf_matrix = tfidf_vectorizer.fit_transform(documents)
        from sklearn.metrics.pairwise import cosine_similarity
        cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix)
        val = [item[1] for item in cosine_sim]
        if question:
            documentsq = (question, actualans)
            tfidf_vectorizer = TfidfVectorizer(stop_words='english')
            tfidf_matrixq = tfidf_vectorizer.fit_transform(documentsq)
            cosine_simq = cosine_similarity(tfidf_matrixq[0:1], tfidf_matrixq)
            valq = [item[1] for item in cosine_simq]
            match_indexq = valq[0]
            if match_indexq > 0.95:
                match_index=0.05
            else:
                match_index=round(val[0], 2)
        else:
            match_index=0
    return match_index*100 + '%'

print(getscorenew(questionv,expectedansv,actualansv));
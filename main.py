import wikipedia, time
import heapq
import mysql.connector as msql
from sys import argv
import wikipedia
import time
# import gensim
import numpy as np
import threading
import datetime
# from scipy import spatial
import facebook_handler

db = msql.connect(host='localhost', user='root', passwd='root')
db.cursor().execute('use wikipedia;')

NAMESPACES = '(0)'


def avg_feature_vector(sentence, model, num_features, index2word_set):
    words = sentence.split()
    feature_vec = np.zeros((num_features,), dtype='float32')
    n_words = 0
    for word in words:
        if word in index2word_set:
            n_words += 1
            feature_vec = np.add(feature_vec, model[word])
    if (n_words > 0):
        feature_vec = np.divide(feature_vec, n_words)
    return feature_vec


def word_distance(a, b):
    sum = 0
    n = 0

    for w1 in a.lower().split():
        if w1 not in index2word_set:
            continue
        for w2 in b.lower().split():
            if w2 not in index2word_set:
                continue
            x = model.similarity(w1, w2)
            n += 1
            sum += x

    if n == 0:
        return 0

    average = sum / n
    return average


def spatial_distance(a, b):
    s1_afv = avg_feature_vector(a.lower(), model=model, num_features=300, index2word_set=index2word_set)
    s2_afv = avg_feature_vector(b.lower(), model=model, num_features=300, index2word_set=index2word_set)
    sim = 1 - spatial.distance.cosine(s1_afv, s2_afv)

    return sim


def heuristic(a, b):
    average = word_distance(a, b)
    return 4 * (1 - average)


def get_id(page):
    csr = db.cursor()
    csr.execute('select page_id from page where page_title=%s and page_namespace in {} limit 1'.format(NAMESPACES),
                (page,))
    res = next(csr, (None,))[0]
    csr.close()
    return res


def r_get_neighbors(x):
    csr = db.cursor()
    query = '''select pl.pl_from from pagelinks pl
               inner join page p
               on p.page_title=pl.pl_title and p.page_namespace=pl.pl_namespace
               where
                   p.page_id=%s and pl.pl_from_namespace=0'''
    csr.execute(query, (x,))
    res = [t[0] for t in csr]
    csr.close()
    return res


def get_neighbors(x):
    csr = db.cursor()
    query = '''select page_id, page_title from page p
                inner join pagelinks pl
                on p.page_title=pl.pl_title and p.page_namespace=pl.pl_namespace
                where
                    pl.pl_from=%s and p.page_namespace=0'''
    csr.execute(query, (x,))
    res = list(csr)
    csr.close()
    return res


def outbound(page_ids):
    if not page_ids:
        return []
    page_ids = str(tuple(page_ids)).replace(',)', ')')
    csr = db.cursor()
    query = '''select pl.pl_from, p.page_id from page p
               inner join pagelinks pl
               on p.page_title=pl.pl_title and p.page_namespace=pl.pl_namespace
               where
                   pl.pl_from in ''' + page_ids + ''' and pl.pl_namespace=0'''
    csr.execute(query)
    res = list(csr)
    csr.close()
    return res


def inbound(page_ids):
    if not page_ids:
        return []
    page_ids = str(tuple(page_ids)).replace(',)', ')')
    csr = db.cursor()
    query = '''select p.page_id, pl.pl_from from pagelinks pl
               inner join page p
               on pl.pl_title=p.page_title and pl.pl_namespace=p.page_namespace
               where
                   p.page_id in ''' + page_ids + ''' and pl.pl_from_namespace=0'''
    csr.execute(query)
    res = list(csr)
    csr.close()
    return res


def count_outbound(pages):
    return len(outbound(pages))


def count_inbound(pages):
    return len(inbound(pages))


def get_title(_id):
    csr = db.cursor()
    csr.execute('select page_title from page where page_id={} limit 1'.format(_id))
    res = next(csr, (None,))[0]
    csr.close()
    return res


def random_page():
    random = wikipedia.random(1)
    try:
        result = wikipedia.page(random)
    except wikipedia.exceptions.DisambiguationError as e:
        result = random_page()
    return result


class PriorityQueue:
    def __init__(self):
        self.elements = []

    def empty(self):
        return len(self.elements) == 0

    def put(self, item, priority):
        heapq.heappush(self.elements, (priority, item))

    def get(self):
        return heapq.heappop(self.elements)[1]


def a_star_search(start, goal, heuristic):
    startID = get_id(start)
    goalID = get_id(goal)
    frontier = PriorityQueue()
    frontier.put((startID, start), 0)
    came_from = {}
    cost_so_far = {}
    came_from[startID] = None
    cost_so_far[startID] = 0

    while not frontier.empty():
        current_id, current = frontier.get()
        if current_id == goalID:
            break

        for next_id, next_title in get_neighbors(current_id):
            new_cost = cost_so_far[current_id] + 1
            if next_id not in cost_so_far or new_cost < cost_so_far[next_id]:
                cost_so_far[next_id] = new_cost

                priority = new_cost + heuristic(goal, next_title)
                print(priority)
                print(next_title)
                frontier.put((next_id, next_title), priority)
                came_from[next_title] = current

    print("finished iteration!")

    came_from_titles = []
    while current is not None:
        came_from_titles.append(current)
        current = came_from.get(current)

    return came_from_titles[::-1], cost_so_far


def get_paths(page_ids, visited_dict):
    paths = []

    for page_id in page_ids:
        if page_id is None:

            return [[]]
        else:

            current_paths = get_paths(visited_dict[page_id],
                                      visited_dict)
            for current_path in current_paths:
                new_path = list(current_path)
                new_path.append(page_id)
                paths.append(new_path)

    return paths


def breadth_first_search(source_page_id, target_page_id, timeout=420):
    # If the source and target page IDs are identical, return the trivial path.
    start_time = time.time()
    target = target_page_id
    source = source_page_id
    if source_page_id == target_page_id:
        return [[source_page_id]]

    paths = []

    unvisited_forward = {source_page_id: [None]}
    unvisited_backward = {target_page_id: [None]}

    # The visited dictionaries are a mapping from page ID to a list of that page's parents' IDs.

    visited_forward = {}
    visited_backward = {}

    # Set the initial forward and backward depths to 0.

    forward_depth = 0
    backward_depth = 0

    while len(paths) == 0:
        done = False

        # Run the next iteration of the breadth first search in whichever direction has the smaller number
        # of links at the next level.
        current_time = time.time()
        if (current_time - start_time) > timeout:
            break
        outgoing_links = outbound(unvisited_forward.keys())
        incoming_links = inbound(unvisited_backward.keys())

        if len(outgoing_links) < len(incoming_links):

            # ---  FORWARD BREADTH FIRST SEARCH  ---#

            forward_depth += 1
            #
            # outgoing_links = \
            #     outbound(unvisited_forward.keys())

            # Mark all of the unvisited forward pages as visited.

            for page_id in unvisited_forward:
                visited_forward[page_id] = unvisited_forward[page_id]

            # Clear the unvisited forward dictionary.

            unvisited_forward.clear()

            for (source_page_id, target_page_id) in outgoing_links:
                current_time = time.time()
                if (current_time - start_time) > timeout:
                    done = True
                    break
                if target_page_id:
                    target_page_id = int(target_page_id)

                    # If the target page is in neither visited forward nor unvisited forward, add it to
                    # unvisited forward.

                    if target_page_id not in visited_forward \
                            and target_page_id not in unvisited_forward:
                        unvisited_forward[target_page_id] = \
                            [source_page_id]
                    elif target_page_id in unvisited_forward:

                        # If the target page is in unvisited forward, add the source page as another one of its
                        # parents.

                        unvisited_forward[target_page_id].append(source_page_id)
                    if target_page_id == target:
                        done = True
                        break
            if done:
                break
        else:

            # ---  BACKWARD BREADTH FIRST SEARCH  ---#

            backward_depth += 1

            # Fetch the pages which can reach the currently unvisited backward pages.

            # incoming_links = \
            #     inbound(unvisited_backward.keys())

            # Mark all of the unvisited backward pages as visited.

            for page_id in unvisited_backward:
                visited_backward[page_id] = unvisited_backward[page_id]

            # Clear the unvisited backward dictionary.

            unvisited_backward.clear()

            for (target_page_id, source_page_id) in incoming_links:
                current_time = time.time()
                if (current_time - start_time) > timeout:
                    done = True
                    break
                if source_page_id:
                    source_page_id = int(source_page_id)

                    # If the source page is in neither visited backward nor unvisited backward, add it to
                    # unvisited backward.

                    if source_page_id not in visited_backward \
                            and source_page_id \
                            not in unvisited_backward:
                        unvisited_backward[source_page_id] = \
                            [target_page_id]
                    elif source_page_id in unvisited_backward:

                        # If the source page is in unvisited backward, add the target page as another one of its
                        # parents.

                        unvisited_backward[source_page_id].append(target_page_id)
                    if source_page_id == source:
                        done = True
                        break
            if done:
                break

        # ---  CHECK FOR PATH COMPLETION  ---#
        # The search is complete if any of the pages are in both unvisited backward and unvisited, so
        # find the resulting paths.
        if time.time() - start_time > timeout:
            return []
        done = False
        for page_id in unvisited_forward:
            if page_id in unvisited_backward:
                paths_from_source = \
                    get_paths(unvisited_forward[page_id],
                              visited_forward)
                paths_from_target = \
                    get_paths(unvisited_backward[page_id],
                              visited_backward)

                for path_from_source in paths_from_source:
                    for path_from_target in paths_from_target:
                        current_path = list(path_from_source) \
                                       + [page_id] \
                                       + list(reversed(path_from_target))

                        # TODO: This line shouldn't be required, but there are some unexpected duplicates.

                        if current_path not in paths:
                            paths.append(current_path)
                            done = True
                            break
                    if done:
                        break
                if done:
                    break
        if done:
            break

    paths = [[get_title(_id) for _id in p] for p in paths]
    return paths


def get_articles():
    src = None
    dst = None
    while src is None:
        try:
            src, dst = wikipedia.random(2)
            src, dst = src.replace(' ', '_'), dst.replace(' ', '_')
        except KeyboardInterrupt:
            pass
        except:
            print('Connection error. Retrying...')
    return src, dst


def postloop(paths):
    posted = False
    empty = False
    while True:
        if datetime.datetime.now().minute % 30 == 0:
            if not paths:
                if not empty:
                    print('No paths found')
                    empty = True
            else:
                if not posted:
                    path = paths.pop(0)
                    path = [" ".join(string.split("_")) for string in path]  # page_name -> [page, name] -> page name
                    first_page = path[0]
                    last_page = path[-1]
                    header = f"finding path between {first_page} and {last_page}:\n"
                    facebook_handler.post_to_facebook(header + "\n".join(path))
                    posted = True
                    empty = False
        else:
            posted = False
        time.sleep(1)


def main():
    times = []
    threshold = int(argv[1])
    paths = []
    worker = threading.Thread(target=postloop, args=(paths,), daemon=True)
    worker.start()
    outfile = open('wikipaths.txt', 'a')
    try:
        i = 1
        while True:
            if len(paths) > 1000:
                continue
            src, dst = get_articles()
            print('%d: %s\t->\t%s' % (i, src, dst))
            before = time.time()
            src_id = get_id(src)
            dst_id = get_id(dst)
            if not (dst_id and src_id):
                print('Could not resolve ID for one or more articles.')
                continue
            searchresult = breadth_first_search(get_id(src), get_id(dst), timeout=threshold)
            paths += searchresult
            print(paths)
            after = time.time()
            elapsed = after - before
            print('Time elapsed: %f' % elapsed)
            times.append(elapsed)
            outfile.write('{}\n'.format(elapsed))
            i += 1
    except KeyboardInterrupt:
        db.close()
        exit()
    times = np.array(times)
    result = np.mean(times < threshold)
    print(r'% of results above threshold: {}%'.format(str(100 * result)))
    print('\7')
    db.close()


if __name__ == '__main__':
    main()

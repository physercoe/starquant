/*
 * Copyright 2009-2016 the original author or authors.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/**
 * @file    _spk_strsep.h
 *
 * Strsep函数的头文件
 *
 * @version $Id$
 * @since   2012/01/05
 */


#ifndef _SPK_STRSEP_H
#define _SPK_STRSEP_H


#include    <sutil/types.h>
#include    <sutil/compiler.h>
#include    <sutil/platform/spk_platforms.h>
#include    <sutil/string/_spk_strpbrk.h>
#include    <sutil/logger/spk_console_masked_log.h>


#ifdef __cplusplus
extern "C" {
#endif


/**
 * extract token from string, and return the end of token
 *
 * 注意：
 * 对于theEnd的处理，要注意是否已考虑到对以下两种特殊情况的处理：
 * 1、delim位于字符串首。这时*theEnd == return
 * 2、若字符串不是以delim结尾的，当最后一次返回时，*theEnd == NULL
 */
static __inline char*
SStr_Strsep2(char **ppString, char **ppTokenEnd, const char *pDelim) {
    char    *pBegin = (char *) NULL;
    char    *pEnd = (char *) NULL;

    SLOG_ASSERT(ppString && pDelim && *pDelim);

    pBegin = *ppString;
    if (unlikely(! pBegin || ! *pBegin)) {
        *ppString = NULL;
        if (ppTokenEnd) {
            *ppTokenEnd = NULL;
        }
        return (char *) pBegin;
    }

    if (pDelim[1] == '\0') {
        if (*pBegin == pDelim[0]) {
            pEnd = pBegin;
        } else {
            pEnd = strchr(pBegin + 1, pDelim[0]);
        }
    } else {
        pEnd = SStr_Strpbrk(pBegin, pDelim);
    }

    if (pEnd) {
        *ppString = pEnd + 1;

        if (ppTokenEnd) {
            *ppTokenEnd = pEnd;
        } else {
            *pEnd = '\0';
        }
    } else {
        *ppString = NULL;

        if (ppTokenEnd) {
            *ppTokenEnd = NULL;
        }
    }

    return pBegin;
}


/**
 * extract token from string
 *
 * If *stringp is  NULL, the strsep() function returns NULL and does
 * nothing else.  Otherwise, this function finds the first token in the
 * string *stringp, where tokens are delimited by symbols in the string
 * delim. This token is terminated with a '\0' character (by overwriting
 * the delimiter) and *stringp  is updated to point past the token.
 * In case no delimiter was found, the token is taken to be the entire
 * string *stringp, and *stringp is made NULL.
 *
 * @return  The strsep() function returns a pointer to the token, that is,
 *          it returns the original value of *stringp.
 * @see     strsep()
 */
static __inline char*
SStr_Strsep(char **stringp, const char *delim) {
    return SStr_Strsep2(stringp, (char **) NULL, delim);
}
/* -------------------------           */


#ifdef __cplusplus
}
#endif

#endif  /* _SPK_STRSEP_H */

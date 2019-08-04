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
 * @file    _spk_strpbrk.h
 *
 * Strpbrk函数的头文件
 *
 * @version $Id$
 * @since   2012/01/05
 */


#ifndef _SPK_STRPBRK_H
#define _SPK_STRPBRK_H


#include    <sutil/types.h>
#include    <sutil/compiler.h>
#include    <sutil/platform/spk_platforms.h>
#include    <sutil/logger/spk_console_masked_log.h>


#ifdef __cplusplus
extern "C" {
#endif


/**
 * check a char is any of a set of characters
 */
static __inline BOOL
SStr_IsAnyChar(const char ch, const char *accept) {
    SLOG_ASSERT(accept);
    while (*accept) {
        if (*accept++ == ch) {
            return TRUE;
        }
    }
    return FALSE;
}


/**
 * check a char is any of a set of characters
 */
static __inline BOOL
SStr_IsAnyChar2(const char ch, const char *accept, int len) {
    SLOG_ASSERT(accept);
    while (*accept && len--) {
        if (*accept++ == ch) {
            return TRUE;
        }
    }
    return FALSE;
}


/**
 * search a string for any of a set of characters
 *
 * The strpbrk() function locates the first occurrence in the string s of any
 * of the characters in the string accept.
 *
 * @return  returns a pointer to the character in s that matches one of the
 *          characters in accept, or NULL if no such character is found.
 * @see     strpbrk()
 */
static __inline char *
SStr_Strpbrk(const char *s, const char *accept) {
    if (unlikely(! s)) {
        return (char *) NULL;
    }

    while (*s) {
        if (SStr_IsAnyChar(*s, accept)) {
            return (char *) s;
        }
        ++s;
    }
    return (char *) NULL;
}


/**
 * search a string for any of a set of characters reverse
 *
 * @return  returns a pointer to the character in s that matches one of the
 *          characters in accept, or NULL if no such character is found.
 */
static __inline char *
SStr_StrpbrkReverse(const char *s, const char *accept) {
    int32   endPos = 0;

    if (unlikely(! s)) {
        return (char *) NULL;
    }

    endPos = strlen(s) - 1;
    while (endPos >= 0) {
        if (SStr_IsAnyChar(s[endPos], accept)) {
            return (char *) &s[endPos];
        }
        endPos--;
    }
    return (char *) NULL;
}
/* -------------------------           */


#ifdef __cplusplus
}
#endif

#endif  /* _SPK_STRPBRK_H */

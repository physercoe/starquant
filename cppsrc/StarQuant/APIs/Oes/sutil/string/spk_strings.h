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
 * @file    spk_strings.h
 *
 * 字符串处理函数的头文件(线程安全)
 *
 * @version $Id$
 * @since   2012/01/05
 */


#ifndef _SPK_STRINGS_H
#define _SPK_STRINGS_H


#include    <sutil/types.h>
#include    <sutil/compiler.h>
#include    <sutil/cmnlib.h>
#include    <sutil/platform/spk_platforms.h>
#include    <sutil/string/spk_string_convert.h>
#include    <sutil/string/spk_string_var.h>
#include    <sutil/string/spk_multi_field_string.h>
#include    <sutil/string/_spk_strncasecmp.h>
#include    <sutil/string/_spk_strpbrk.h>
#include    <sutil/string/_spk_strsep.h>
#include    <sutil/string/_spk_strchcmp.h>
#include    <sutil/string/spk_fixed_snprintf.h>
#include    <sutil/string/spk_strverscmp.h>
#include    <sutil/logger/spk_console_masked_log.h>


#ifdef __cplusplus
extern "C" {
#endif


/* ===================================================================
 * 函数声明
 * =================================================================== */

/*
 * 替换目标字符串中的待替换字符串
 */
char*   SStr_Replace(char *pBuf, const char *pTarget, const char *pOldStr,
            const char *pNewStr);

/*
 * 替换目标字符串中的待替换字符串(可指定替换个数)
 */
char*   SStr_ReplaceAppointed(char *pBuf, const char *pTarget,
            const char *pOldStr, const char *pNewStr, int32 n);

/*
 * 取得被前、后缀包裹的字符串
 */
char*   SStr_GetWrappedString(char *pBuf, const char *pTarget,
            const char *pPrefix, const char *pPostfix);

/*
 * 构造被前、后缀包裹的字符串
 */
char*   SStr_BuildWrappedString(char *pBuf, const char *pTarget,
            int32 targetLen, const char *pPrefix, const char *pPostfix);

/*
 * 返回字符串是否是以指定的字符串起始的
 */
BOOL    SStr_IsStartWith(const char *pStr, const char *pStartWith,
            const char *pAnyChar, int32 n);

/*
 * 返回字符串是否是以指定的字符串起始的 (忽略大小写)
 */
BOOL    SStr_IsIgnoreCaseStartWith(const char *pStr, const char *pStartWith,
            const char *pAnyChar, int32 n);

/*
 * 统计字符串中指定字符出现的次数
 */
int32   SStr_TotalChars(const char *pStr, const char *pChars);
/* -------------------------           */


/* ===================================================================
 * 跨平台处理
 * =================================================================== */

#if defined (__WINDOWS__)
#   undef   snprintf
#   define  snprintf                SStr_Snprintf
#endif
/* -------------------------           */


/* ===================================================================
 * Inline 函数
 * =================================================================== */

/**
 * 返回字符串是否是空字符串
 *
 * @param   pStr    待校验字符串
 * @return  TRUE, 为空; FALSE, 不为空
 */
static __inline BOOL
SStr_IsEmpty(const char *pStr) {
    return (! (pStr && *pStr));
}


/**
 * 返回字符串是否是空字符串
 *
 * @param   pStr    待校验字符串
 * @return  TRUE, 为空; FALSE, 不为空
 */
static __inline BOOL
SStr_IsBlank(const char *pStr) {
    if (pStr) {
        while (*pStr) {
            if (! SPK_ISSPACE(*pStr)) {
                return FALSE;
            }
            pStr ++;
        }
    }
    return TRUE;
}


/**
 * 若字符串为空则返回指定的值
 */
static __inline const char*
SStr_SwitchBlankStr(const char *s, const char *v) {
    return SStr_IsBlank(s) ? v : s;
}


/**
 * 返回跳过左端空格后的字符串
 *
 * @param   pStr    字符串
 * @return  跳过左端空格后的字符串指针
 */
static __inline const char*
SStr_Ltrim(const char *pStr) {
    if (unlikely(! pStr)) {
        return (const char *) NULL;
    }

    while (SPK_ISSPACE(*pStr)) {
        pStr++;
    }
    return pStr;
}


/**
 * 跳过字符串起始的空格和'0'
 *
 * @param   pStr    字符串
 * @return  跳过左端空格和'0'后的字符串指针
 */
static __inline const char*
SStr_LtrimZero(const char *pStr) {
    const char  *pPtr = pStr;

    if (unlikely(! pStr)) {
        return (const char *) NULL;
    }

    while (SPK_ISSPACE(*pStr) || *pStr == '0') {
        pStr++;
    }

    if ((*pStr == 'x' || *pStr == '.') && pStr > pPtr) {
        pStr--;
    }
    return pStr;
}


/**
 * 去除字符串右端的空格
 *
 * @param   pStr    字符串
 * @return  去除空格后的字符串
 */
static __inline char*
SStr_RtrimRude(char *pStr) {
    int32   endPos = 0;

    if (unlikely(! pStr)) {
        return (char *) NULL;
    }

    endPos = strlen(pStr) - 1;
    while (endPos >= 0 && SPK_ISSPACE(pStr[endPos])) {
        endPos--;
    }

    pStr[++endPos] = '\0';
    return pStr;
}


/**
 * 去除字符串前后端的空格
 *
 * @param   pStr    字符串
 * @return  去除空格后的字符串
 */
static __inline char*
SStr_TrimRude(char *pStr) {
    return SStr_RtrimRude((char *) SStr_Ltrim(pStr));
}


/**
 * 返回转换为大写后的字符串
 */
static __inline char*
SStr_ToUpper(char *pStr) {
    char    *pPtr = pStr;

    if (unlikely(! pStr)) {
        return (char *) NULL;
    }

    while (*pPtr) {
        *pPtr = SPK_TOUPPER((int32) *pPtr);
        pPtr ++;
    }
    return pStr;
}


/**
 * 返回转换为大写后的字符串
 */
static __inline char*
SStr_ToUpperR(char *pBuf, const char *pStr) {
    int32   j = 0;

    SLOG_ASSERT(pBuf);
    if (unlikely(! pStr)) {
        *pBuf = '\0';
        return pBuf;
    }

    while (pStr[j]) {
        pBuf[j] = SPK_TOUPPER((int32) pStr[j]);
        j++;
    }
    pBuf[j] = '\0';

    return pBuf;
}


/**
 * 返回转换为小写后的字符串
 */
static __inline char*
SStr_ToLower(char *pStr) {
    char    *pPtr = pStr;

    if (unlikely(! pStr)) {
        return (char *) NULL;
    }

    while (*pPtr != '\0') {
        *pPtr = SPK_TOLOWER((int32) *pPtr);
        pPtr ++;
    }
    return pStr;
}


/**
 * 返回转换为小写后的字符串
 */
static __inline char*
SStr_ToLowerR(char *pBuf, const char *pStr) {
    char    *pPtr = pBuf;
    int32   j = 0;

    SLOG_ASSERT(pBuf);
    if (unlikely(! pStr)) {
        *pBuf = '\0';
        return pBuf;
    }

    while (pStr[j]) {
        pPtr[j] = SPK_TOLOWER((int32) pStr[j]);
        j++;
    }

    pPtr[j] = '\0';
    return pPtr;
}


/**
 * 拷贝指定长度的字符串
 * <p>需保证缓存有足够的空间(maxStrlen + 1)</p>
 *
 * @param   maxStrlen   最大有效字符长度(不包括结尾的'\0')，即buf的长度需至少
 *                      为 maxStrlen + 1
 */
static __inline char*
SStr_StrCopy(char *pBuf, const char *pStr, int32 maxStrlen) {
    SLOG_ASSERT(pBuf);

    if (likely(pStr && maxStrlen > 0)) {
        strncpy(pBuf, pStr, maxStrlen);
        pBuf[maxStrlen] = '\0';
    } else {
        *pBuf = '\0';
    }
    return pBuf;
}


/**
 * 连接两个字符串到新字符串中
 * <p>需保证缓存有足够的空间(maxStrlen + 1)</p>
 *
 * @param   maxStrlen   最大有效字符长度(不包括结尾的'\0')，即buf的长度需至少
 *                      为 maxStrlen + 1
 */
static __inline char*
SStr_StrCat(char *pBuf, const char *s1, const char *s2, int32 maxStrlen) {
    SLOG_ASSERT(pBuf);

    if (likely(s1)) {
        SStr_StrCopy(pBuf, s1, maxStrlen);
    } else {
        *pBuf = '\0';
    }

    if (likely(s2)) {
        return strncat(pBuf, s2, maxStrlen - strlen(pBuf));
    }
    return pBuf;
}


/**
 * 连接字符串并将字符串指针移动到新字符串末尾
 *
 * @return 原字符串地址
 */
static __inline char*
SStr_StrCatP(char **ppString, const char *s) {
    char    *pBegin = (char *) NULL;
    char    *pEnd = (char *) NULL;

    if (unlikely(! ppString || ! *ppString)) {
        return (char *) NULL;
    } else if (unlikely(! s)) {
        return *ppString;
    } else {
        pBegin = pEnd = *ppString;
    }

    while (*pEnd) {
        pEnd++;
    }

    while (*s) {
        *pEnd++ = *s++;
    }

    *pEnd = '\0';
    *ppString = pEnd;

    return pBegin;
}


/**
 * 连接字符和字符串
 * <p>需保证缓存有足够的空间(maxStrlen + 1)</p>
 *
 * @param   maxStrlen   参数 pStr 的最大字符串长度，buf的长度需至少为 maxStrlen + 1
 */
static __inline char*
SStr_StrCatChStr(char *pBuf, char ch, const char *pStr, int32 maxStrlen) {
    SLOG_ASSERT(pBuf && pStr);

    *pBuf = ch;
    memcpy(pBuf + 1, pStr, maxStrlen);

    pBuf[maxStrlen + 1] = '\0';
    return pBuf;
}


/**
 * 拷贝字符串并去除空格
 * <p>需保证缓存有足够的空间(maxStrlen + 1)</p>
 *
 * @param   maxStrlen   最大有效字符长度(不包括结尾的'\0')，即buf的长度需至少
 *                      为 maxStrlen + 1
 */
static __inline char*
SStr_StrTrimCopy(char *pBuf, const char *pStr, int32 maxStrlen) {
    char    *pPtr = pBuf;

    SLOG_ASSERT(pPtr);
    if (unlikely(! pStr)) {
        *pBuf = '\0';
        return pBuf;
    }

    while (SPK_ISSPACE(*pStr)) {
        pStr++;
    }

    while (*pStr && maxStrlen-- != 0) {
        *pPtr++ = *pStr++;
    }

    do {
        pPtr--;
    } while (pPtr >= pBuf && SPK_ISSPACE(*pPtr));

    pPtr++;
    *pPtr = '\0';

    return pBuf;
}


/**
 * 先拷贝字符串再去除空格
 * <p>需保证缓存有足够的空间(maxStrlen + 1)</p>
 *
 * @param   maxStrlen   最大有效字符长度(不包括结尾的'\0')，即buf的长度需至少
 *                      为 maxStrlen + 1
 */
static __inline char*
SStr_StrFixedLengthTrimCopy(char *pBuf, const char *pStr, int32 maxStrlen) {
    char    *pPtr = pBuf;

    SLOG_ASSERT(pPtr);
    if (unlikely(! pStr)) {
        *pBuf = '\0';
        return pBuf;
    }

    while (SPK_ISSPACE(*pStr) && maxStrlen != 0) {
        pStr++;
        maxStrlen--;
    }

    while (*pStr && maxStrlen-- != 0) {
        *pPtr++ = *pStr++;
    }

    do {
        pPtr--;
    } while (pPtr >= pBuf && SPK_ISSPACE(*pPtr));

    pPtr++;
    *pPtr = '\0';

    return pBuf;
}


/**
 * 以右对齐的方式拷贝字符串并去除空格
 * <p>需保证缓存有足够的空间(maxlen + 1)</p>
 *
 * @param   maxlen      最大有效字符长度(不包括结尾的'\0')，即buf的长度需至少
 *                      为 maxlen + 1
 */
static __inline char*
SStr_StrRightAlignmentCopy(char *pBuf, const char *pStr, int32 maxlen,
        char leftFiller) {
    const char  *pPtr = (const char *) NULL;
    int32       len = maxlen;

    if (unlikely(maxlen <= 0)) {
        return SStr_StrTrimCopy(pBuf, pStr, maxlen);
    }

    SLOG_ASSERT(pBuf);
    if (unlikely(! pStr)) {
        *pBuf = '\0';
        return pBuf;
    }

    while (SPK_ISSPACE(*pStr)) {
        pStr++;
    }

    pPtr = pStr;
    while (*pPtr && len != 0) {
        pPtr++;
        len--;
    }

    do {
        pPtr--;
        len++;
    } while (len <= maxlen && SPK_ISSPACE(*pPtr));
    len--;

    memset(pBuf, leftFiller, len);
    memcpy(pBuf + len, pStr, maxlen - len);

    pBuf[maxlen] = '\0';
    return pBuf;
}


/**
 * 跳过空字符
 */
static __inline char*
SStr_SkipSpaces(char **ppStr) {
    SLOG_ASSERT(ppStr);

    while (SPK_ISSPACE(**ppStr)) {
        (*ppStr) ++;
    }
    return *ppStr;
}


/**
 * 从字符串末端反向跳过空字符
 */
static __inline void
SStr_SkipSpacesReverse(char **ppEnd, char *pBegin) {
    char    *pOriginEnd;

    SLOG_ASSERT(ppEnd);

    pOriginEnd = *ppEnd;
    while (*ppEnd > pBegin && SPK_ISSPACE(**ppEnd)) {
        (*ppEnd) --;
    }

    if (*ppEnd < pOriginEnd) {
        *((*ppEnd) + 1) = '\0';
    }

    if (SPK_ISSPACE(**ppEnd)) {
        **ppEnd = '\0';
    } else {
        (*ppEnd) ++;
    }
}


/**
 * 跳过所有字符直到指定的字符串末尾
 *
 * @param   ppStr       <in/out: char**> 待处理字符串的指针的指针
 * @param   pSkipKey    <char*> 待跳过的字符串指针
 * @return  小于0, 未找到指定的字符串; 大于等于0, 已跳过字符串的起始位置(相对值)
 */
static __inline int32
SStr_SkipString(char **ppStr, const char *pSkipKey) {
    char    *pStrFound = (char*) NULL;
    int32   offset = 0;

    SLOG_ASSERT(ppStr && pSkipKey);

    if (! (pStrFound = strstr(*ppStr, pSkipKey))) {
        return NEG(ENOENT);
    }

    offset = pStrFound - *ppStr;
    *ppStr = pStrFound + strlen(pSkipKey);

    return offset;
}


/**
 * 替换字符串中的指定字符
 *
 * @param   pStr    待处理的字符串
 * @return  已替换的字符数量
 */
static __inline int32
SStr_ReplaceChar(char *pStr, const char c1, const char c2, int32 n) {
    int32   count = 0;

    SLOG_ASSERT(pStr);

    while (*pStr && n) {
        if (*pStr == c1) {
            *pStr = c2;
            n--;
            count++;
        }
        pStr ++;
    }
    return count;
}


/**
 * 从后面开始替换字符串中的指定字符
 *
 * @param   pStr    待处理的字符串
 * @return
 */
static __inline int32
SStr_ReplaceCharReverse(char *pStr, const char c1, const char c2, int32 n) {
    int32   endPos = 0;
    int32   count = 0;

    SLOG_ASSERT(pStr);

    endPos = strlen(pStr) - 1;
    while (endPos >= 0 && n) {
        if (pStr[endPos] == c1) {
            pStr[endPos] = c2;
            n--;
            count++;
        }
        endPos--;
    }
    return count;
}
/* -------------------------           */


#ifdef __cplusplus
}
#endif

#endif  /* _SPK_STRINGS_H */

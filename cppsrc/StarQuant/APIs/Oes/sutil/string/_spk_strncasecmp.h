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
 * @file    _spk_strncasecmp.h
 *
 * Strncasecmp函数的头文件
 *
 * @version $Id$
 * @since   2012/01/05
 */


#ifndef _SPK_STRNCASECMP_H
#define _SPK_STRNCASECMP_H


#include    <sutil/types.h>


#ifdef __cplusplus
extern "C" {
#endif


/*
 * compare two strings ignoring case
 */
int     SStr_Strncasecmp(const char *s1, const char *s2, int n);
/* -------------------------           */


#ifdef __cplusplus
}
#endif

#endif  /* _SPK_STRNCASECMP_H */


package de.finatix.v2

import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlin.random.Random
import kotlin.time.Duration.Companion.milliseconds

private const val RANDOM_DELAY_UPPER_BOUND_MILLIS: Long = 500

/**
 * Diff v1→v2: introduce immutable Number object to replace Pair, use more kotlin specific syntax
 */
suspend fun main() {
    val limit = 100

    coroutineScope {
        IntRange(1, limit)
            .map { Number(it) }
            .map { async { it.process() } }
            .forEach { println(it.await()) }
    }
}

class Number
private constructor(
    private val value: Int,
    private val out: String
) {
    constructor(v: Int) : this(v, "")

    suspend fun process(): String {
        val result = this
            .check(3, "Fizz")
            .check(5, "Buzz")
            .check(7, "Bazz")
            .final()

        delay(Random.nextLong(RANDOM_DELAY_UPPER_BOUND_MILLIS).milliseconds)
        return result
    }

    private fun check(divisor: Int, replacement: String): Number {
        return if (this.value % divisor == 0) {
            Number(this.value, this.out + replacement)
        } else {
            this
        }
    }

    private fun final(): String {
        return this.out.ifBlank {
            this.value.toString()
        }
    }
}
